from __future__ import annotations

from hashlib import md5
import logging
from pathlib import Path
import re

import chromadb
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import Settings

SUPPORTED_SUFFIXES = {".pdf", ".txt", ".text", ".md"}
TOKEN_RE = re.compile(r"[a-z0-9]+")
logger = logging.getLogger(__name__)


class SimpleHashEmbeddings:
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = TOKEN_RE.findall(text.lower())
        if not tokens:
            return vector
        for token in tokens:
            slot = int(md5(token.encode("utf-8")).hexdigest(), 16) % self.dimensions
            vector[slot] += 1.0
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]


def sanitize_metadata(metadata: dict) -> dict[str, str | int | float | bool]:
    clean: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[str(key)] = value
        else:
            clean[str(key)] = str(value)
    return clean


def normalize_corpus_name(corpus_name: str) -> str:
    normalized = "-".join(corpus_name.strip().split()).lower()
    if not normalized:
        raise ValueError("Corpus name cannot be empty.")
    return normalized


def supported_files_in(input_dir: Path) -> list[Path]:
    return [path for path in sorted(input_dir.rglob("*")) if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES]


def load_documents(input_dir: Path) -> tuple[list[Document], list[Path]]:
    files = supported_files_in(input_dir)
    documents: list[Document] = []
    for file_path in files:
        loader = PyPDFLoader(str(file_path)) if file_path.suffix.lower() == ".pdf" else TextLoader(str(file_path), autodetect_encoding=True)
        for index, document in enumerate(loader.load()):
            document.metadata = sanitize_metadata({
                **document.metadata,
                "source": str(file_path.resolve()),
                "source_name": file_path.name,
                "source_type": "pdf" if file_path.suffix.lower() == ".pdf" else "text",
                "loader_document_index": index,
                "page": document.metadata.get("page"),
            })
            documents.append(document)
    return documents, files


def split_documents(documents: list[Document], settings: Settings) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks, start=1):
        chunk.metadata["chunk_id"] = f"chunk-{index:05d}"
        chunk.metadata = sanitize_metadata(chunk.metadata)
    return chunks


def build_embeddings(settings: Settings):
    provider = settings.embedding_provider.lower()
    if provider in {"demo", "local"}:
        logger.info("Using demo/local hash embeddings")
        return SimpleHashEmbeddings()
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI embeddings.")
        logger.info("Using OpenAI embeddings model '%s'", settings.embedding_model)
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            check_embedding_ctx_length=False,
        )
    raise ValueError(f"Unsupported embedding provider for this OpenAI build: {settings.embedding_provider}")


def build_llm(settings: Settings):
    provider = settings.llm_provider.lower()
    if provider == "demo":
        raise ValueError("Demo mode does not create an LLM-backed chain.")
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using the OpenAI chat model.")
        logger.info("Using OpenAI chat model '%s'", settings.openai_model)
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=settings.llm_temperature,
        )
    raise ValueError(f"Unsupported LLM provider for this OpenAI build: {settings.llm_provider}")


def reset_collection(settings: Settings, corpus_name: str) -> None:
    client = chromadb.PersistentClient(path=str(settings.chroma_dir.resolve()))
    collection_name = settings.collection_name_for(corpus_name)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass


def get_vector_store(settings: Settings, corpus_name: str, embeddings) -> Chroma:
    return Chroma(
        collection_name=settings.collection_name_for(corpus_name),
        persist_directory=str(settings.chroma_dir.resolve()),
        embedding_function=embeddings,
    )


def build_conversational_chain(settings: Settings, corpus_name: str, top_k: int):
    embeddings = build_embeddings(settings)
    llm = build_llm(settings)
    vector_store = get_vector_store(settings, corpus_name, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})

    contextualize_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Rewrite the latest user question into a standalone search query using the chat history only for "
                "reference resolution. Do not answer the question.",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_prompt)

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a document-grounded Q&A assistant.\n"
                "Use only the retrieved context below to answer the user.\n"
                "If the answer is not explicitly supported by the context, reply exactly with: I don't know.\n"
                "When possible, cite the supporting source names in square brackets.\n\n"
                "Retrieved context:\n{context}",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    qa_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(history_aware_retriever, qa_chain)


def retrieval_preview(settings: Settings, corpus_name: str, question: str, top_k: int) -> list[tuple[Document, float]]:
    embeddings = build_embeddings(settings)
    vector_store = get_vector_store(settings, corpus_name, embeddings)
    return vector_store.similarity_search_with_score(question, k=top_k)


def serialize_history(messages: list[BaseMessage]) -> list[dict[str, str]]:
    payload: list[dict[str, str]] = []
    for message in messages:
        role = "assistant" if message.type == "ai" else "user"
        payload.append({"role": role, "content": str(message.content)})
    return payload
