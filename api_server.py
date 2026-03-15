#!/usr/bin/env python3
"""HTTP API for the Swiggy RAG System.

This server exposes a small JSON API that can be consumed by the static
GitHub Pages UI located in web/.
"""

from dataclasses import asdict
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.config import RAGConfig
from core.factory import ConfigurationError, create_rag_system

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Swiggy RAG API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = None
bootstrap_error = None


class IngestRequest(BaseModel):
    file_path: str = Field(min_length=1)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)


def _build_config() -> RAGConfig:
    """Build config from env with safe local defaults for API usage."""
    config = RAGConfig.from_env()
    if config.llm_provider == "openai" and not config.openai_api_key:
        config.llm_provider = "ollama"
        if config.llm_model_name == "gpt-3.5-turbo":
            config.llm_model_name = "llama3.2"
    return config


@app.on_event("startup")
def startup() -> None:
    global orchestrator, bootstrap_error

    try:
        config = _build_config()
        orchestrator = create_rag_system(config=config)
        bootstrap_error = None
        logger.info("RAG API initialized successfully")
    except Exception as exc:  # pylint: disable=broad-except
        bootstrap_error = str(exc)
        orchestrator = None
        logger.exception("Failed to initialize RAG API")


@app.get("/health")
def health() -> dict[str, Any]:
    if bootstrap_error:
        return {"status": "error", "message": bootstrap_error}

    assert orchestrator is not None
    return {
        "status": "ok",
        "ready": orchestrator.validate_system_ready(),
    }


@app.post("/ingest")
def ingest_document(payload: IngestRequest) -> dict[str, Any]:
    if bootstrap_error or orchestrator is None:
        raise HTTPException(status_code=503, detail=bootstrap_error or "System not initialized")

    result = orchestrator.ingest_document(payload.file_path)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message or "Ingestion failed")

    return asdict(result)


@app.post("/query")
def query_document(payload: QueryRequest) -> dict[str, Any]:
    if bootstrap_error or orchestrator is None:
        raise HTTPException(status_code=503, detail=bootstrap_error or "System not initialized")

    try:
        result = orchestrator.process_query(payload.question)
    except (ValueError, ConfigurationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    answer = result.answer
    return {
        "answer": {
            "text": answer.text,
            "confidence": answer.confidence,
            "supporting_chunks": [
                {
                    "similarity_score": round(item.similarity_score, 4),
                    "source_document": item.chunk.metadata.source_document,
                    "chunk_index": item.chunk.metadata.chunk_index,
                    "text_preview": item.chunk.text[:280],
                }
                for item in answer.supporting_chunks
            ],
        },
        "processing_time_seconds": round(result.processing_time_seconds, 3),
        "retrieved_chunks": len(answer.supporting_chunks),
    }
