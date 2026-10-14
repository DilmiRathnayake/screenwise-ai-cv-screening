"""RAG-style semantic search: embed documents/queries and query vector store."""

from __future__ import annotations

import time
from typing import List, Optional

from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.models import (
    EmbedDocument,
    SemanticSearchHit,
    SemanticSearchRequest,
    SemanticSearchResponse,
    UpsertEmbeddingsRequest,
    UpsertEmbeddingsResponse,
)
from app.services.vector_store import VectorStore
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class RagService:
    def __init__(
        self,
        embeddings: Optional[EmbeddingRepository] = None,
        store: Optional[VectorStore] = None,
    ) -> None:
        self.embeddings = embeddings or EmbeddingRepository()
        self.store = store or VectorStore()

    @property
    def backend(self) -> str:
        return self.store.backend

    def upsert(self, request: UpsertEmbeddingsRequest) -> UpsertEmbeddingsResponse:
        started = time.perf_counter()
        docs: List[EmbedDocument] = request.documents
        if not docs:
            return UpsertEmbeddingsResponse(
                upserted=0, backend=self.backend, processing_ms=0
            )

        texts = [d.text or " " for d in docs]
        vectors = self.embeddings.encode(texts)
        ids = [d.id for d in docs]
        metas = [d.metadata for d in docs]
        count = self.store.upsert(ids, vectors, metas, texts)
        elapsed = (time.perf_counter() - started) * 1000
        return UpsertEmbeddingsResponse(
            upserted=count,
            backend=self.backend,
            processing_ms=round(elapsed, 2),
        )

    def search(self, request: SemanticSearchRequest) -> SemanticSearchResponse:
        started = time.perf_counter()
        qvec = self.embeddings.encode([request.query])[0]
        raw = self.store.search(
            qvec, top_k=request.top_k, metadata_filter=request.filter
        )
        results = [
            SemanticSearchHit(
                id=h["id"],
                score=round(float(h["score"]), 4),
                metadata=h.get("metadata") or {},
                text_preview=h.get("text_preview"),
            )
            for h in raw
        ]
        elapsed = (time.perf_counter() - started) * 1000
        return SemanticSearchResponse(
            query=request.query,
            backend=self.backend,
            total=len(results),
            results=results,
            processing_ms=round(elapsed, 2),
        )

    def delete(self, ids: List[str]) -> int:
        return self.store.delete(ids)
