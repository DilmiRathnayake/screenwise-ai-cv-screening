"""Load calibrated LightGBM ranker for Model 02."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from app.configs.settings import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class RankerRepository:
    """Optional ML ranker loaded from models/ranking/."""

    def __init__(self, model_dir: Optional[Path] = None) -> None:
        self.settings = get_settings()
        self.model_dir = Path(model_dir or self.settings.ranking_model_path)
        self._model = None
        self._calibration: dict = {}
        self._load()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def calibration(self) -> dict:
        return dict(self._calibration)

    def _load(self) -> None:
        cal_path = self.model_dir / "calibration.json"
        if cal_path.exists():
            try:
                self._calibration = json.loads(cal_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Failed to load calibration.json: %s", exc)

        model_path = self.model_dir / "lgbm_ranker.pkl"
        if not model_path.exists():
            logger.info("LightGBM ranker not found at %s — using rule-based scoring only", model_path)
            return
        try:
            import joblib

            self._model = joblib.load(model_path)
            logger.info("Loaded LightGBM ranker from %s", model_path)
        except Exception as exc:
            logger.warning("Failed to load LightGBM ranker: %s", exc)
            self._model = None

    def predict_score(self, features: np.ndarray, feature_names: Optional[list] = None) -> Optional[float]:
        if self._model is None:
            return None
        try:
            names = feature_names or self._calibration.get("feature_names")
            if names and len(names) == len(features):
                import pandas as pd

                X = pd.DataFrame([features], columns=names)
            else:
                X = features.reshape(1, -1)
            if hasattr(self._model, "predict_proba"):
                proba = self._model.predict_proba(X)[0]
                return float(proba[1]) if len(proba) > 1 else float(proba[0])
            pred = self._model.predict(X)
            return float(pred[0])
        except Exception as exc:
            logger.warning("LightGBM prediction failed: %s", exc)
            return None

    def get_semantic_fusion_weight(self, default: float) -> float:
        return float(self._calibration.get("semantic_fusion_weight", default))

    def get_ml_blend_weight(self, default: float = 0.0) -> float:
        if not self.is_loaded:
            return 0.0
        return float(self._calibration.get("ml_blend_weight", default))

    def get_shortlist_threshold(self, default: float) -> float:
        return float(self._calibration.get("shortlist_threshold", default))
