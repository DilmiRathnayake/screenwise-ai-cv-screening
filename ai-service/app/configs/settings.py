"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CV Screening AI Service"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    datasets_dir: Path = Field(
        default=Path(r"D:\cv screening system"),
        description="Path to legacy Kaggle datasets and NER JSON",
    )

    it_ner_datasets_dir: Path = Field(
        default=Path(r"D:\cv screening\ScreenWise_IT_Datasets_ner"),
        description="ScreenWise IT NER dataset directory",
    )
    it_ranking_datasets_dir: Path = Field(
        default=Path(r"D:\cv screening\ScreenWise_IT_Datasets_ranking"),
        description="ScreenWise IT ranking dataset directory",
    )
    processed_datasets_dir: Path = Field(
        default=BASE_DIR / "datasets" / "processed",
        description="Cleaned/preprocessed dataset copies",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    ner_model_path: Path = BASE_DIR / "models" / "extraction" / "ner_model"
    ranking_model_path: Path = BASE_DIR / "models" / "ranking"
    model2_metrics_path: Path = Field(
        default=BASE_DIR.parent / "model2_it" / "evaluation" / "model2_metrics.json",
        description="Held-out test metrics from the Model 2 IT LambdaMART pipeline",
    )
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # Pinecone / local vector store (RAG semantic search)
    pinecone_api_key: str = ""
    pinecone_index_name: str = "cv-screening"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    local_vector_path: Path = BASE_DIR / "models" / "vectors" / "local_index.npz"

    tesseract_cmd: str = ""
    ocr_language: str = "eng"
    max_upload_mb: int = 25
    max_bulk_files: int = 100

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ner_json_path(self) -> Path:
        return self.datasets_dir / "Entity Recognition in Resumes.json"

    @property
    def resume_data_csv(self) -> Path:
        return self.datasets_dir / "resume_data.csv"

    @property
    def ai_screening_csv(self) -> Path:
        return self.datasets_dir / "AI_Resume_Screening.csv"

    @property
    def updated_resume_csv(self) -> Path:
        return self.datasets_dir / "UpdatedResumeDataSet.csv"

    def _it_ner_source(self) -> Path:
        processed = self.processed_datasets_dir / "ner"
        return processed if processed.exists() else self.it_ner_datasets_dir

    def _it_ranking_source(self) -> Path:
        processed = self.processed_datasets_dir / "ranking"
        return processed if processed.exists() else self.it_ranking_datasets_dir

    @property
    def it_ner_train_path(self) -> Path:
        return self._it_ner_source() / "it_ner_train.json"

    @property
    def it_ner_val_path(self) -> Path:
        return self._it_ner_source() / "it_ner_val.json"

    @property
    def it_ner_test_path(self) -> Path:
        return self._it_ner_source() / "it_ner_test.json"

    @property
    def it_ner_full_path(self) -> Path:
        return self._it_ner_source() / "it_ner_full.json"

    @property
    def it_cv_texts_csv(self) -> Path:
        return self.it_ner_datasets_dir / "it_cv_texts.csv"

    @property
    def it_candidates_train_csv(self) -> Path:
        return self._it_ranking_source() / "it_train.csv"

    @property
    def it_candidates_val_csv(self) -> Path:
        return self._it_ranking_source() / "it_val.csv"

    @property
    def it_candidates_test_csv(self) -> Path:
        return self._it_ranking_source() / "it_test.csv"

    @property
    def it_candidates_full_csv(self) -> Path:
        return self._it_ranking_source() / "it_candidates_full.csv"

    @property
    def it_job_descriptions_csv(self) -> Path:
        return self._it_ranking_source() / "it_job_descriptions.csv"

    @property
    def it_candidate_job_matches_csv(self) -> Path:
        return self._it_ranking_source() / "it_candidate_job_matches.csv"


@lru_cache
def get_settings() -> Settings:
    return Settings()
