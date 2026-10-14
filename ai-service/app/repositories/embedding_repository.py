"""Embedding model repository for semantic similarity."""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from app.configs.settings import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingRepository:
    """Lazy-load SentenceTransformer for section-aware embeddings."""

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.settings = get_settings()
        self.model_name = model_name or self.settings.embedding_model_name
        self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _ensure_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading embedding model: %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                logger.error("Failed to load embedding model: %s", exc)
                raise
        return self._model

    def encode(self, texts: List[str]) -> np.ndarray:
        model = self._ensure_model()
        cleaned = [t if t and t.strip() else " " for t in texts]
        vectors = model.encode(cleaned, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype=np.float32)

    def cosine_similarity(self, a: str, b: str) -> float:
        vecs = self.encode([a, b])
        return float(np.dot(vecs[0], vecs[1]))

    def section_similarity(self, job_text: str, sections: dict[str, str]) -> dict[str, float]:
        """Compute cosine similarity of job text vs each CV section."""
        keys = list(sections.keys())
        values = [sections[k] or " " for k in keys]
        if not keys:
            return {}
        job_vec = self.encode([job_text])[0]
        section_vecs = self.encode(values)
        scores = {}
        for i, key in enumerate(keys):
            scores[key] = float(np.dot(job_vec, section_vecs[i]))
        return scores
