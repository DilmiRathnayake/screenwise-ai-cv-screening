"""Feature extraction for IT candidate-job ranking (LightGBM)."""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from app.schemas.models import CandidateProfile, JobRequirements
from app.utils.it_skills import normalize_it_skill

FEATURE_NAMES = [
    "skill_overlap_ratio",
    "skill_overlap_count",
    "missing_skill_ratio",
    "experience_ratio",
    "experience_meets_min",
    "education_level",
    "project_count_norm",
    "cert_count_norm",
    "communication_score",
    "semantic_similarity",
    "skills_criterion",
    "experience_criterion",
    "projects_criterion",
    "education_criterion",
    "certifications_criterion",
    "rule_based_score",
]

DEGREE_LEVELS = {
    "phd": 5,
    "doctor": 5,
    "master": 4,
    "msc": 4,
    "mba": 4,
    "bachelor": 3,
    "bsc": 3,
    "ba": 3,
    "diploma": 2,
    "certificate": 1,
}


def match_skills(required: List[str], candidate: List[str]) -> tuple[List[str], List[str]]:
    req = [s for s in required if s]
    cand_map = {normalize_it_skill(s): s for s in candidate if s}
    matched: List[str] = []
    missing: List[str] = []
    for r in req:
        rn = normalize_it_skill(r)
        hit = False
        for cn, orig in cand_map.items():
            if not rn or not cn:
                continue
            if rn == cn or (len(rn) > 2 and (rn in cn or cn in rn)):
                matched.append(orig)
                hit = True
                break
        if not hit:
            missing.append(r)
    return matched, missing


def education_level(profile: CandidateProfile) -> float:
    level = 0
    blob = " ".join(f"{e.degree or ''} {e.field or ''}" for e in profile.education).lower()
    for key, val in DEGREE_LEVELS.items():
        if key in blob:
            level = max(level, val)
    return float(level) / 5.0


def build_features(
    profile: CandidateProfile,
    job: JobRequirements,
    criterion_scores: Dict[str, float],
    semantic: float,
    rule_score: float,
) -> np.ndarray:
    req = job.required_skills or []
    matched, missing = match_skills(req, profile.technical_skills or [])
    overlap_ratio = len(matched) / len(req) if req else 0.5
    missing_ratio = len(missing) / len(req) if req else 0.0

    years = float(profile.years_of_experience or 0.0)
    min_exp = float(job.minimum_experience or 0.0)
    exp_ratio = min(1.5, years / min_exp) if min_exp > 0 else min(1.0, years / 8.0)
    exp_meets = 1.0 if years >= min_exp else 0.0

    proj_norm = min(1.0, len(profile.projects or []) / 5.0)
    cert_norm = min(1.0, len(profile.certifications or []) / 4.0)
    comm = float(profile.communication_score or 0.5)

    return np.array(
        [
            overlap_ratio,
            len(matched),
            missing_ratio,
            exp_ratio,
            exp_meets,
            education_level(profile),
            proj_norm,
            cert_norm,
            comm,
            max(0.0, min(1.0, semantic)),
            criterion_scores.get("technical_skills", 0.0),
            criterion_scores.get("experience", 0.0),
            criterion_scores.get("projects", 0.0),
            criterion_scores.get("education", 0.0),
            criterion_scores.get("certifications", 0.0),
            rule_score,
        ],
        dtype=np.float32,
    )
