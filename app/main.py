from __future__ import annotations

from functools import partial
from pathlib import Path
import logging

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.schemas import AdminOverview, ChatRequest, ChatResponse, CorpusBuildRequest, HealthResponse, IngestResponse, RetrievalPreviewRequest
from app.service import ConversationalRagService

logger = logging.getLogger(__name__)

settings = get_settings()

allowed_origins = {
    settings.frontend_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
}

app = FastAPI(title="Document Q&A Assistant", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_service(settings: Settings = Depends(get_settings)) -> ConversationalRagService:
    return ConversationalRagService(settings)


@app.get("/api/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        default_corpus=settings.default_corpus,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.active_embedding_model(),
        llm_provider=settings.llm_provider,
        llm_model=settings.active_llm_model(),
        frontend_origin=settings.frontend_origin,
    )


@app.get("/api/corpora")
def list_corpora(service: ConversationalRagService = Depends(get_service)):
    return service.list_corpora()


@app.get("/api/admin/overview", response_model=AdminOverview)
def admin_overview(service: ConversationalRagService = Depends(get_service)) -> AdminOverview:
    return AdminOverview(corpora=service.list_corpora(), sessions=service.list_sessions())


@app.get("/api/admin/documents")
def admin_documents(corpus_name: str = Query(..., min_length=1), service: ConversationalRagService = Depends(get_service)):
    try:
        return service.get_documents(corpus_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/admin/corpus-detail", response_model=IngestResponse)
def admin_corpus_detail(
    corpus_name: str = Query(..., min_length=1),
    service: ConversationalRagService = Depends(get_service),
) -> IngestResponse:
    try:
        return service.get_corpus_detail(corpus_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/admin/chunks")
def admin_chunks(
    corpus_name: str = Query(..., min_length=1),
    limit: int = Query(default=60, ge=1, le=300),
    service: ConversationalRagService = Depends(get_service),
):
    try:
        return service.get_chunks(corpus_name, limit)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/admin/sessions")
def admin_sessions(service: ConversationalRagService = Depends(get_service)):
    return service.list_sessions()


@app.post("/api/admin/retrieve-preview")
def admin_retrieve_preview(payload: RetrievalPreviewRequest, service: ConversationalRagService = Depends(get_service)):
    try:
        return service.preview_retrieval(corpus_name=payload.corpus_name, question=payload.question, top_k=payload.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/corpora/build", response_model=IngestResponse)
def build_corpus(payload: CorpusBuildRequest, service: ConversationalRagService = Depends(get_service)) -> IngestResponse:
    try:
        return service.build_corpus(
            corpus_name=payload.corpus_name,
            input_dir=Path(payload.input_dir),
            force_rebuild=payload.force_rebuild,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /api/corpora/build")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/corpora/upload-build", response_model=IngestResponse)
async def upload_and_build_corpus(
    corpus_name: str = Form(""),
    force_rebuild: bool = Form(False),
    replace_existing: bool = Form(True),
    files: list[UploadFile] = File(...),
    service: ConversationalRagService = Depends(get_service),
) -> IngestResponse:
    try:
        payload: list[tuple[str, bytes]] = []
        for file in files:
            payload.append((file.filename or "upload.bin", await file.read()))
        build_call = partial(
            service.upload_and_build_corpus,
            corpus_name=corpus_name,
            files=payload,
            force_rebuild=force_rebuild,
            replace_existing=replace_existing,
        )
        return await run_in_threadpool(build_call)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /api/corpora/upload-build")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    service: ConversationalRagService = Depends(get_service),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    corpus_name = payload.corpus_name or settings.default_corpus
    try:
        response = service.chat(
            question=payload.question,
            corpus_name=corpus_name,
            session_id=payload.session_id,
            top_k=payload.top_k or settings.default_top_k,
        )
        return ChatResponse(**response)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /api/chat")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/chat/{session_id}/history")
def chat_history(session_id: str, service: ConversationalRagService = Depends(get_service)):
    return service.history_for(session_id)
