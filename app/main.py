from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.schemas import BuildResponse, ChatRequest, ChatResponse, CorpusBuildRequest, HealthResponse
from app.service import RagFaqService

app = FastAPI(title="RAG ChatBot FAQs", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_service(settings: Settings = Depends(get_settings)) -> RagFaqService:
    return RagFaqService(settings)


@app.get("/api/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        default_corpus=settings.default_corpus,
        embedding_backend=settings.embedding_backend,
        ollama_chat_enabled=bool(settings.ollama_chat_model),
    )


@app.get("/api/corpora")
def list_corpora(service: RagFaqService = Depends(get_service)):
    return service.list_corpora()


@app.post("/api/corpora/build", response_model=BuildResponse)
def build_corpus(payload: CorpusBuildRequest, service: RagFaqService = Depends(get_service)) -> BuildResponse:
    try:
        return service.build_corpus(
            corpus_name=payload.corpus_name,
            input_dir=Path(payload.input_dir).expanduser().resolve(),
            force_rebuild=payload.force_rebuild,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, service: RagFaqService = Depends(get_service), settings: Settings = Depends(get_settings)) -> ChatResponse:
    corpus_name = payload.corpus_name or settings.default_corpus
    try:
        answer, citations = service.answer_question(
            question=payload.question,
            corpus_name=corpus_name,
            top_k=payload.top_k or settings.default_top_k,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ChatResponse(
        answer=answer,
        corpus_name=corpus_name,
        retrieval_count=len(citations),
        citations=citations,
    )
