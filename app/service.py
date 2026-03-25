from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from app.config import Settings
from app.embeddings import build_embedding_model
from app.generation import AnswerGenerator
from app.ingestion import ChunkRecord, dump_manifest, load_file, sha256_for_file, supported_files_in
from app.retrieval import HybridRetriever
from app.schemas import BuildResponse, CorpusRecord, RetrievalHit, UploadBuildResponse
from app.vector_store import ChromaVectorStore


class RagFaqService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = build_embedding_model(settings)
        self.generator = AnswerGenerator(settings)

    def build_corpus(self, *, corpus_name: str, input_dir: Path, force_rebuild: bool = False) -> BuildResponse:
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
        files = supported_files_in(input_dir)
        if not files:
            raise ValueError("No supported files were found in the input directory.")

        collection_name = self.settings.collection_name_for(corpus_name)
        corpus_dir = self.settings.corpora_dir / corpus_name
        manifest_path = corpus_dir / "manifest.json"
        manifest_files = [{"path": str(path.relative_to(input_dir)), "sha256": sha256_for_file(path)} for path in files]
        vector_store = ChromaVectorStore(
            persist_directory=str(self.settings.chroma_dir.resolve()),
            collection_name=collection_name,
        )

        if manifest_path.exists() and not force_rebuild:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            if existing.get("files") == manifest_files and vector_store.count() > 0:
                return BuildResponse(
                    corpus_name=corpus_name,
                    collection_name=collection_name,
                    input_dir=str(input_dir),
                    indexed_files=len(files),
                    chunk_count=existing.get("chunk_count", 0),
                    skipped=True,
                    manifest_path=str(manifest_path),
                )

        vector_store.reset()

        chunk_records: list[ChunkRecord] = []
        for file_path in files:
            chunk_records.extend(
                load_file(
                    file_path,
                    chunk_size=self.settings.chunk_size,
                    chunk_overlap=self.settings.chunk_overlap,
                )
            )
        if not chunk_records:
            raise ValueError("Supported files were found, but no extractable text could be indexed.")

        payload = [{"id": chunk.chunk_id, "text": chunk.text, "metadata": chunk.metadata} for chunk in chunk_records]
        embeddings = self.embeddings.embed_documents([chunk.text for chunk in chunk_records])
        vector_store.add_chunks(payload, embeddings)

        built_at = datetime.now(UTC).isoformat()
        manifest = {
            "corpus_name": corpus_name,
            "input_dir": str(input_dir),
            "collection_name": collection_name,
            "indexed_files": len(files),
            "chunk_count": len(chunk_records),
            "last_built_at": built_at,
            "files": manifest_files,
        }
        dump_manifest(manifest_path, manifest)

        return BuildResponse(
            corpus_name=corpus_name,
            collection_name=collection_name,
            input_dir=str(input_dir),
            indexed_files=len(files),
            chunk_count=len(chunk_records),
            skipped=False,
            manifest_path=str(manifest_path),
        )

    def upload_and_build_corpus(
        self,
        *,
        corpus_name: str,
        files: list[tuple[str, bytes]],
        force_rebuild: bool = False,
        replace_existing: bool = True,
    ) -> UploadBuildResponse:
        if not files:
            raise ValueError("At least one file must be uploaded.")

        corpus_slug = self._normalize_corpus_name(corpus_name)
        target_dir = self.settings.incoming_dir / corpus_slug
        if replace_existing and target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        uploaded_files: list[str] = []
        for original_name, content in files:
            safe_name = Path(original_name).name.strip()
            if not safe_name:
                continue
            destination = target_dir / safe_name
            destination.write_bytes(content)
            uploaded_files.append(safe_name)

        if not uploaded_files:
            raise ValueError("Uploaded files were empty or invalid.")

        result = self.build_corpus(corpus_name=corpus_slug, input_dir=target_dir, force_rebuild=force_rebuild)
        return UploadBuildResponse(**result.model_dump(), uploaded_files=uploaded_files)

    def list_corpora(self) -> list[CorpusRecord]:
        records: list[CorpusRecord] = []
        for manifest in sorted(self.settings.corpora_dir.glob("*/manifest.json")):
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            records.append(
                CorpusRecord(
                    corpus_name=payload["corpus_name"],
                    input_dir=payload["input_dir"],
                    collection_name=payload["collection_name"],
                    indexed_files=payload["indexed_files"],
                    chunk_count=payload["chunk_count"],
                    last_built_at=payload["last_built_at"],
                )
            )
        return records

    def answer_question(self, *, question: str, corpus_name: str, top_k: int) -> tuple[str, list[RetrievalHit]]:
        collection_name = self.settings.collection_name_for(self._normalize_corpus_name(corpus_name))
        vector_store = ChromaVectorStore(
            persist_directory=str(self.settings.chroma_dir.resolve()),
            collection_name=collection_name,
        )
        retriever = HybridRetriever(vector_store, self.embeddings)
        hits = retriever.search(question, top_k=top_k)
        answer = self.generator.answer(question, hits)
        citations = [
            RetrievalHit(
                chunk_id=hit.chunk_id,
                source_file=str(hit.metadata.get("source_file", "unknown")),
                source_type=str(hit.metadata.get("source_type", "unknown")),
                score=round(hit.score, 4),
                snippet=hit.text[:500],
                metadata=hit.metadata,
            )
            for hit in hits
        ]
        return answer, citations

    @staticmethod
    def _normalize_corpus_name(corpus_name: str) -> str:
        normalized = "-".join(corpus_name.strip().split()).lower()
        if not normalized:
            raise ValueError("Corpus name cannot be empty.")
        return normalized
