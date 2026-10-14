"""Controllers for extraction, ranking, and semantic search endpoints."""

from __future__ import annotations

import json
import time
from typing import List

from fastapi import UploadFile

from app.configs.ranking_weights import CRITERIA, get_industry_weights, list_industries
from app.configs.settings import get_settings
from app.schemas.models import (
    BulkExtractItem,
    BulkExtractResponse,
    ExtractResponse,
    HealthResponse,
    RankRequest,
    RankResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    UpsertEmbeddingsRequest,
    UpsertEmbeddingsResponse,
    WeightsResponse,
)
from app.services.extraction_service import ExtractionService
from app.services.rag_service import RagService
from app.services.ranking_service import RankingService


class AIController:
    def __init__(
        self,
        extraction: ExtractionService | None = None,
        ranking: RankingService | None = None,
        rag: RagService | None = None,
    ) -> None:
        self.settings = get_settings()
        self.extraction = extraction or ExtractionService()
        self.ranking = ranking or RankingService()
        self.rag = rag or RagService(embeddings=self.ranking.embeddings)

    def health(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            version=self.settings.app_version,
            ner_model_loaded=self.extraction.ner_loaded,
            embedding_model_loaded=self.ranking.embedding_loaded,
            vector_backend=self.rag.backend,
        )

    async def extract(self, file: UploadFile) -> ExtractResponse:
        content = await file.read()
        self._validate_size(content)
        filename = file.filename or "upload.bin"
        return self.extraction.extract_from_bytes(filename, content)

    async def extract_bulk(self, files: List[UploadFile]) -> BulkExtractResponse:
        if len(files) > self.settings.max_bulk_files:
            raise ValueError(
                f"Too many files. Max bulk upload is {self.settings.max_bulk_files}."
            )
        started = time.perf_counter()
        results: List[BulkExtractItem] = []
        for file in files:
            filename = file.filename or "upload.bin"
            try:
                content = await file.read()
                self._validate_size(content)
                resp = self.extraction.extract_from_bytes(filename, content)
                results.append(
                    BulkExtractItem(filename=filename, success=True, profile=resp.profile)
                )
            except Exception as exc:
                results.append(
                    BulkExtractItem(filename=filename, success=False, error=str(exc))
                )
        elapsed = (time.perf_counter() - started) * 1000
        return BulkExtractResponse(
            success=True,
            total=len(results),
            results=results,
            processing_ms=round(elapsed, 2),
        )

    def rank(self, request: RankRequest) -> RankResponse:
        if not request.candidates:
            raise ValueError("At least one candidate is required.")
        return self.ranking.rank(request)

    def weights(self, industry: str) -> WeightsResponse:
        return WeightsResponse(
            industry=industry,
            weights=get_industry_weights(industry),
            criteria=list(CRITERIA),
        )

    def industries(self) -> dict:
        return {"industries": list_industries() + ["default"]}

    def model2_metrics(self) -> dict:
        """Return held-out test metrics from model2_it/evaluation/model2_metrics.json."""
        path = self.settings.model2_metrics_path
        if not path.exists():
            return {
                "available": False,
                "message": f"Model 2 metrics not found at {path}. Run model2_it/evaluate_model2.py.",
            }
        data = json.loads(path.read_text(encoding="utf-8"))
        data["available"] = True
        data["source"] = str(path)
        return data

    def upsert_embeddings(
        self, request: UpsertEmbeddingsRequest
    ) -> UpsertEmbeddingsResponse:
        return self.rag.upsert(request)

    def semantic_search(
        self, request: SemanticSearchRequest
    ) -> SemanticSearchResponse:
        if not request.query.strip():
            raise ValueError("Query is required.")
        return self.rag.search(request)

    def delete_embeddings(self, ids: List[str]) -> dict:
        removed = self.rag.delete(ids)
        return {"success": True, "removed": removed, "backend": self.rag.backend}

    def _validate_size(self, content: bytes) -> None:
        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise ValueError(f"File exceeds max size of {self.settings.max_upload_mb} MB.")
