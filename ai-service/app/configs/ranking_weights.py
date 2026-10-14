"""IT recruitment ranking weight templates (ScreenWise IT dataset aligned)."""

from copy import deepcopy
from typing import Dict

CRITERIA = (
    "technical_skills",
    "experience",
    "projects",
    "education",
    "communication",
    "certifications",
)

# Dataset formula: Skills 35% + Exp 25% + Edu 15% + Comm 10% + Proj 10% + Cert 5%
INDUSTRY_WEIGHTS: Dict[str, Dict[str, float]] = {
    "it": {
        "technical_skills": 0.35,
        "experience": 0.25,
        "education": 0.15,
        "communication": 0.10,
        "projects": 0.10,
        "certifications": 0.05,
    },
    "default": {
        "technical_skills": 0.35,
        "experience": 0.25,
        "education": 0.15,
        "communication": 0.10,
        "projects": 0.10,
        "certifications": 0.05,
    },
}

# Semantic fusion ratio (tuned on validation set)
SEMANTIC_FUSION_WEIGHT = 0.12
SHORTLIST_THRESHOLD = 0.60


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Ensure all criteria present and sum to 1.0."""
    merged = {c: float(weights.get(c, 0.0)) for c in CRITERIA}
    total = sum(merged.values())
    if total <= 0:
        return deepcopy(INDUSTRY_WEIGHTS["it"])
    return {k: v / total for k, v in merged.items()}


def get_industry_weights(industry: str) -> Dict[str, float]:
    key = (industry or "it").strip().lower().replace(" ", "_")
    aliases = {
        "information_technology": "it",
        "tech": "it",
        "software": "it",
    }
    key = aliases.get(key, key)
    if key not in INDUSTRY_WEIGHTS:
        key = "it"
    return normalize_weights(INDUSTRY_WEIGHTS[key])


def list_industries() -> list[str]:
    return ["it"]
