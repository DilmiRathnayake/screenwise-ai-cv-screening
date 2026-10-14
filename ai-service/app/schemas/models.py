"""Pydantic schemas for extraction and ranking APIs."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EducationEntry(BaseModel):
    university: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[str] = None
    field: Optional[str] = None


class ExperienceEntry(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class ProjectEntry(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    communication_score: float = Field(default=0.5, ge=0.0, le=1.0)
    raw_text: Optional[str] = None
    extraction_meta: Dict[str, Any] = Field(default_factory=dict)


class ExtractResponse(BaseModel):
    success: bool = True
    filename: str
    profile: CandidateProfile
    processing_ms: float


class BulkExtractItem(BaseModel):
    filename: str
    success: bool
    profile: Optional[CandidateProfile] = None
    error: Optional[str] = None


class BulkExtractResponse(BaseModel):
    success: bool = True
    total: int
    results: List[BulkExtractItem]
    processing_ms: float


class JobRequirements(BaseModel):
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)
    minimum_experience: float = 0.0
    education_level: Optional[str] = None
    industry: str = "default"
    required_certifications: List[str] = Field(default_factory=list)
    ranking_weights: Optional[Dict[str, float]] = None
    communication_importance: Optional[float] = None


class RankCandidateInput(BaseModel):
    candidate_id: Optional[str] = None
    profile: CandidateProfile
    raw_text: Optional[str] = None


class CriterionScore(BaseModel):
    criterion: str
    score: float
    weight: float
    weighted_score: float
    explanation: str


class RankingExplanationDetail(BaseModel):
    summary: str = ""
    criteria: Dict[str, float] = Field(default_factory=dict)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    experience_relevance: Optional[str] = None
    education_relevance: Optional[str] = None
    project_relevance: Optional[str] = None


class RankedCandidate(BaseModel):
    candidate_id: Optional[str] = None
    name: Optional[str] = None
    matching_percentage: float
    candidate_score: float
    ranking_position: int
    criterion_scores: List[CriterionScore]
    ranking_explanation: str
    explanation: RankingExplanationDetail = Field(default_factory=RankingExplanationDetail)
    semantic_similarity: float = 0.0


class RankRequest(BaseModel):
    job: JobRequirements
    candidates: List[RankCandidateInput]


class RankResponse(BaseModel):
    success: bool = True
    job_title: str
    industry: str
    weights_used: Dict[str, float]
    total_candidates: int
    top_candidates: List[RankedCandidate]
    processing_ms: float


class WeightsResponse(BaseModel):
    industry: str
    weights: Dict[str, float]
    criteria: List[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    ner_model_loaded: bool
    embedding_model_loaded: bool
    vector_backend: str = "local"


class EmbedDocument(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpsertEmbeddingsRequest(BaseModel):
    documents: List[EmbedDocument]


class UpsertEmbeddingsResponse(BaseModel):
    success: bool = True
    upserted: int
    backend: str
    processing_ms: float


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    top_k: int = Field(default=10, ge=1, le=50)
    filter: Optional[Dict[str, Any]] = None


class SemanticSearchHit(BaseModel):
    id: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    text_preview: Optional[str] = None


class SemanticSearchResponse(BaseModel):
    success: bool = True
    query: str
    backend: str
    total: int
    results: List[SemanticSearchHit]
    processing_ms: float
