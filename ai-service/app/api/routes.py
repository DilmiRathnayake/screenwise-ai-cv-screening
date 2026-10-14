"""API routes for AI service."""

from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.controllers.ai_controller import AIController
from app.schemas.models import (
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

router = APIRouter(prefix="/api/v1")

_controller: AIController | None = None


def get_controller() -> AIController:
    global _controller
    if _controller is None:
        _controller = AIController()
    return _controller


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health(controller: AIController = Depends(get_controller)):
    return controller.health()


@router.post("/extract", response_model=ExtractResponse, tags=["Extraction"])
async def extract_cv(
    file: UploadFile = File(..., description="CV file (PDF, DOCX, PNG, JPEG)"),
    controller: AIController = Depends(get_controller),
):
    """Extract structured candidate profile from a single CV."""
    return await controller.extract(file)


@router.post("/extract/bulk", response_model=BulkExtractResponse, tags=["Extraction"])
async def extract_bulk(
    files: List[UploadFile] = File(..., description="Multiple CV files"),
    controller: AIController = Depends(get_controller),
):
    """Extract profiles from multiple CVs (bulk upload)."""
    return await controller.extract_bulk(files)


@router.post("/rank", response_model=RankResponse, tags=["Ranking"])
def rank_candidates(
    request: RankRequest,
    controller: AIController = Depends(get_controller),
):
    """Rank one or more candidates against a job description."""
    return controller.rank(request)


@router.post("/rank/batch", response_model=RankResponse, tags=["Ranking"])
def rank_batch(
    request: RankRequest,
    controller: AIController = Depends(get_controller),
):
    """Alias for batch ranking (same payload as /rank)."""
    return controller.rank(request)


@router.get("/ranking/weights/{industry}", response_model=WeightsResponse, tags=["Ranking"])
def ranking_weights(industry: str, controller: AIController = Depends(get_controller)):
    """Return industry-specific ranking weight template."""
    return controller.weights(industry)


@router.get("/ranking/industries", tags=["Ranking"])
def ranking_industries(controller: AIController = Depends(get_controller)):
    return controller.industries()


@router.get("/ranking/model2/metrics", tags=["Ranking"])
def model2_ranking_metrics(controller: AIController = Depends(get_controller)):
    """Held-out test metrics for Model 2 IT LambdaMART ranker."""
    return controller.model2_metrics()


@router.post(
    "/embeddings/upsert",
    response_model=UpsertEmbeddingsResponse,
    tags=["Semantic Search"],
)
def upsert_embeddings(
    request: UpsertEmbeddingsRequest,
    controller: AIController = Depends(get_controller),
):
    """Index candidate/job text embeddings into Pinecone or local vector store."""
    return controller.upsert_embeddings(request)


@router.post(
    "/search",
    response_model=SemanticSearchResponse,
    tags=["Semantic Search"],
)
def semantic_search(
    request: SemanticSearchRequest,
    controller: AIController = Depends(get_controller),
):
    """Natural-language semantic search over indexed candidates (RAG retrieval)."""
    return controller.semantic_search(request)


@router.delete("/embeddings", tags=["Semantic Search"])
def delete_embeddings(
    ids: List[str] = Query(..., description="Vector IDs to delete"),
    controller: AIController = Depends(get_controller),
):
    return controller.delete_embeddings(ids)
