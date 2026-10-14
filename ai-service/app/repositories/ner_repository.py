"""NER model loading and inference repository."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.configs.settings import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Map dataset labels → schema-friendly labels
LABEL_MAP = {
    "Name": "NAME",
    "Email Address": "EMAIL",
    "Skills": "SKILL",
    "Degree": "DEGREE",
    "College Name": "COLLEGE",
    "Companies worked at": "COMPANY",
    "Designation": "DESIGNATION",
    "Location": "LOCATION",
    "Graduation Year": "GRAD_YEAR",
    "Years of Experience": "YOE",
    "Certification": "CERTIFICATION",
}

NER_LABELS = sorted(set(LABEL_MAP.values()) | {"CERTIFICATION"})


class NERRepository:
    """Load spaCy NER model if available; otherwise return empty predictions."""

    def __init__(self, model_path: Optional[Path] = None) -> None:
        self.settings = get_settings()
        self.model_path = Path(model_path or self.settings.ner_model_path)
        self.nlp = None
        self._load()

    @property
    def is_loaded(self) -> bool:
        return self.nlp is not None

    def _load(self) -> None:
        if not self.model_path.exists():
            logger.warning("NER model not found at %s — using rule-only extraction", self.model_path)
            return
        try:
            import spacy

            self.nlp = spacy.load(str(self.model_path))
            logger.info("Loaded NER model from %s", self.model_path)
        except Exception as exc:
            logger.error("Failed to load NER model: %s", exc)
            self.nlp = None

    def reload(self) -> bool:
        self.nlp = None
        self._load()
        return self.is_loaded

    def predict(self, text: str) -> Dict[str, List[str]]:
        """Return dict of label → unique entity texts."""
        result: Dict[str, List[str]] = {v: [] for v in NER_LABELS}
        if not self.nlp or not text:
            return result

        # spaCy has a practical length limit; chunk long resumes
        max_len = getattr(self.nlp, "max_length", 1_000_000)
        chunk_size = min(100_000, max_len - 1)
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

        for chunk in chunks:
            doc = self.nlp(chunk)
            for ent in doc.ents:
                label = ent.label_
                # Accept either mapped or raw labels
                key = label if label in result else LABEL_MAP.get(label)
                if not key:
                    continue
                value = ent.text.strip()
                if value and value not in result[key]:
                    result[key].append(value)
        return result

    def predict_spans(self, text: str) -> List[Tuple[int, int, str, str]]:
        """Return (start, end, label, text) for evaluation."""
        if not self.nlp or not text:
            return []
        doc = self.nlp(text[: min(len(text), getattr(self.nlp, "max_length", 1_000_000) - 1)])
        return [(ent.start_char, ent.end_char, ent.label_, ent.text) for ent in doc.ents]
