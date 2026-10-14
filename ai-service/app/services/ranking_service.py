"""Intelligent candidate ranking: semantic similarity + weighted multi-criteria scoring."""

from __future__ import annotations

import re
import time
from typing import Dict, List, Optional, Tuple

from app.configs.ranking_weights import (
    SEMANTIC_FUSION_WEIGHT,
    get_industry_weights,
    normalize_weights,
)
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.ranker_repository import RankerRepository
from app.services.ranking_features import build_features
from app.utils.it_skills import normalize_it_skill
from app.schemas.models import (
    CandidateProfile,
    CriterionScore,
    JobRequirements,
    RankCandidateInput,
    RankedCandidate,
    RankRequest,
    RankResponse,
    RankingExplanationDetail,
)
from app.utils.logging_config import get_logger
from app.utils.text_cleaning import normalize_for_matching

logger = get_logger(__name__)

DEGREE_LEVELS = {
    "phd": 5,
    "doctor": 5,
    "master": 4,
    "msc": 4,
    "mba": 4,
    "bachelor": 3,
    "bsc": 3,
    "ba": 3,
    "undergraduate": 3,
    "diploma": 2,
    "certificate": 1,
    "high school": 1,
}


class RankingService:
    def __init__(
        self,
        embeddings: Optional[EmbeddingRepository] = None,
        ranker: Optional[RankerRepository] = None,
    ) -> None:
        self.embeddings = embeddings or EmbeddingRepository()
        self.ranker = ranker if ranker is not None else RankerRepository()
        self._tune_semantic_w: Optional[float] = None
        self._tune_ml_blend_w: Optional[float] = None

    @property
    def embedding_loaded(self) -> bool:
        return self.embeddings.is_loaded

    def rank(self, request: RankRequest) -> RankResponse:
        started = time.perf_counter()
        job = request.job
        weights = self._resolve_weights(job)
        job_blob = self._job_text(job)
        ranked: List[RankedCandidate] = []

        for item in request.candidates:
            profile = item.profile
            raw = item.raw_text or profile.raw_text or self._profile_text(profile)
            ranked.append(
                self._score_candidate(
                    candidate_id=item.candidate_id,
                    profile=profile,
                    raw_text=raw,
                    job=job,
                    job_blob=job_blob,
                    weights=weights,
                )
            )

        ranked.sort(key=lambda c: c.candidate_score, reverse=True)
        for i, cand in enumerate(ranked, start=1):
            cand.ranking_position = i

        elapsed = (time.perf_counter() - started) * 1000
        return RankResponse(
            success=True,
            job_title=job.title,
            industry=job.industry or "it",
            weights_used=weights,
            total_candidates=len(ranked),
            top_candidates=ranked,
            processing_ms=round(elapsed, 2),
        )

    def _resolve_weights(self, job: JobRequirements) -> Dict[str, float]:
        if job.ranking_weights:
            weights = normalize_weights(job.ranking_weights)
        else:
            weights = get_industry_weights(job.industry or "it")
        if job.communication_importance is not None:
            boost = max(0.0, min(1.0, float(job.communication_importance)))
            weights["communication"] = max(weights["communication"], boost)
            weights = normalize_weights(weights)
        return weights

    def _score_candidate(
        self,
        candidate_id: Optional[str],
        profile: CandidateProfile,
        raw_text: str,
        job: JobRequirements,
        job_blob: str,
        weights: Dict[str, float],
        semantic_w: Optional[float] = None,
        ml_blend_w: Optional[float] = None,
    ) -> RankedCandidate:
        components = self._score_components(profile, raw_text, job, job_blob, weights)
        criterion_raw = components["criterion_raw"]
        semantic = components["semantic"]
        matched_skills = components["matched_skills"]
        missing_skills = components["missing_skills"]
        criterion_scores = components["criterion_scores"]
        rule_final = components["rule_final"]
        exp_rel = components["exp_rel"]
        edu_rel = components["edu_rel"]
        proj_rel = components["proj_rel"]
        explanations = components["explanations"]

        sem_w = semantic_w if semantic_w is not None else self._tune_semantic_w
        if sem_w is None:
            sem_w = self.ranker.get_semantic_fusion_weight(SEMANTIC_FUSION_WEIGHT)
        ml_w = ml_blend_w if ml_blend_w is not None else self._tune_ml_blend_w
        if ml_w is None:
            ml_w = self.ranker.get_ml_blend_weight(0.0)

        ml_score = None
        if self.ranker.is_loaded and ml_w > 0:
            features = build_features(profile, job, criterion_raw, semantic, rule_final)
            ml_score = self.ranker.predict_score(features)

        base = rule_final
        if ml_score is not None and ml_w > 0:
            base = (1.0 - ml_w) * rule_final + ml_w * max(0.0, min(1.0, ml_score))

        fused = (1.0 - sem_w) * base + sem_w * max(0.0, min(1.0, semantic))
        match_pct = round(fused * 100, 2)

        strengths = []
        gaps = []
        for c in sorted(criterion_scores, key=lambda x: x.score, reverse=True)[:2]:
            if c.score >= 0.6:
                strengths.append(f"Strong {c.criterion.replace('_', ' ')} ({c.score:.0%})")
        for c in sorted(criterion_scores, key=lambda x: x.score):
            if c.score < 0.5:
                gaps.append(f"Gap in {c.criterion.replace('_', ' ')} ({c.score:.0%})")
        if matched_skills:
            strengths.insert(0, f"Matched IT skills: {', '.join(matched_skills[:5])}")
        if missing_skills:
            gaps.insert(0, f"Missing skills: {', '.join(missing_skills[:5])}")

        summary = (
            f"Overall match {match_pct}% for '{job.title}' (IT). "
            f"Semantic similarity={semantic:.2f}. "
            + ", ".join(
                f"{c.criterion}={c.score:.2f}"
                for c in sorted(criterion_scores, key=lambda x: x.weighted_score, reverse=True)[:3]
            )
            + "."
        )

        display_name = profile.name.strip() if profile.name and profile.name.strip() else None

        return RankedCandidate(
            candidate_id=candidate_id,
            name=display_name,
            matching_percentage=match_pct,
            candidate_score=round(fused, 4),
            ranking_position=0,
            criterion_scores=criterion_scores,
            ranking_explanation=summary,
            explanation=RankingExplanationDetail(
                summary=summary,
                criteria={k: round(v, 4) for k, v in criterion_raw.items()},
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                strengths=strengths[:4],
                gaps=gaps[:4],
                experience_relevance=exp_rel,
                education_relevance=edu_rel,
                project_relevance=proj_rel,
            ),
            semantic_similarity=round(float(semantic), 4),
        )

    def _score_components(
        self,
        profile: CandidateProfile,
        raw_text: str,
        job: JobRequirements,
        job_blob: str,
        weights: Dict[str, float],
    ) -> dict:
        sections = {
            "skills": ", ".join(profile.technical_skills),
            "experience": " ".join(
                f"{e.job_title or ''} {e.company or ''} {e.description or ''}"
                for e in profile.experience
            ),
            "education": " ".join(
                f"{e.degree or ''} {e.university or ''} {e.field or ''}"
                for e in profile.education
            ),
            "projects": " ".join(
                f"{p.name or ''} {p.description or ''} {' '.join(p.technologies)}"
                for p in profile.projects
            ),
            "full": raw_text or self._profile_text(profile),
        }

        try:
            section_sims = self.embeddings.section_similarity(job_blob, sections)
            semantic = float(section_sims.get("full", 0.0))
        except Exception as exc:
            logger.warning("Embedding failed, using lexical fallback: %s", exc)
            section_sims = {}
            semantic = self._lexical_overlap(job_blob, sections["full"])

        matched_skills, missing_skills = self._match_skills(
            job.required_skills, profile.technical_skills
        )
        skills_score = self._skills_score(
            job.required_skills, profile.technical_skills, section_sims.get("skills", semantic)
        )
        experience_score = self._experience_score(
            job.minimum_experience,
            profile.years_of_experience,
            section_sims.get("experience", semantic),
        )
        education_score = self._education_score(
            job.education_level, profile, section_sims.get("education", semantic)
        )
        projects_score = self._projects_score(
            job.required_skills, profile, section_sims.get("projects", 0.0)
        )
        communication_score = float(profile.communication_score or 0.5)
        certifications_score = self._certifications_score(
            job.required_certifications, profile.certifications
        )

        criterion_raw = {
            "technical_skills": skills_score,
            "experience": experience_score,
            "projects": projects_score,
            "education": education_score,
            "communication": communication_score,
            "certifications": certifications_score,
        }

        exp_rel = (
            f"{profile.years_of_experience or 0} years vs required {job.minimum_experience} years"
        )
        edu_blob = " ".join(f"{e.degree or ''}" for e in profile.education) or "not specified"
        edu_rel = f"Candidate education: {edu_blob}; required: {job.education_level or 'any'}"
        proj_rel = (
            f"{len(profile.projects)} projects; tech overlap score {projects_score:.2f}"
        )

        explanations = {
            "technical_skills": self._explain_skills(matched_skills, missing_skills, skills_score),
            "experience": f"Experience relevance: {exp_rel} (score={experience_score:.2f}).",
            "projects": proj_rel,
            "education": f"Education relevance: {edu_rel} (score={education_score:.2f}).",
            "communication": f"Communication proxy score {communication_score:.2f}.",
            "certifications": (
                f"Certification match {certifications_score:.2f} "
                f"({len(profile.certifications)} listed)."
            ),
        }

        criterion_scores: List[CriterionScore] = []
        rule_final = 0.0
        for key, weight in weights.items():
            score = float(criterion_raw[key])
            weighted = score * weight
            rule_final += weighted
            criterion_scores.append(
                CriterionScore(
                    criterion=key,
                    score=round(score, 4),
                    weight=round(weight, 4),
                    weighted_score=round(weighted, 4),
                    explanation=explanations[key],
                )
            )

        return {
            "criterion_raw": criterion_raw,
            "semantic": semantic,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "criterion_scores": criterion_scores,
            "rule_final": rule_final,
            "exp_rel": exp_rel,
            "edu_rel": edu_rel,
            "proj_rel": proj_rel,
            "explanations": explanations,
        }

    def _normalize_skill(self, skill: str) -> str:
        return normalize_it_skill(skill) or normalize_for_matching(skill).replace(" ", "")

    def _match_skills(
        self, required: List[str], candidate: List[str]
    ) -> Tuple[List[str], List[str]]:
        req = [s for s in required if s]
        cand_norm = {self._normalize_skill(s): s for s in candidate if s}
        matched: List[str] = []
        missing: List[str] = []
        for r in req:
            rn = self._normalize_skill(r)
            hit = False
            for cn, orig in cand_norm.items():
                if rn == cn or (len(rn) > 2 and (rn in cn or cn in rn)):
                    matched.append(orig)
                    hit = True
                    break
            if not hit:
                missing.append(r)
        return matched, missing

    def _job_text(self, job: JobRequirements) -> str:
        parts = [
            job.title,
            job.description,
            "skills: " + ", ".join(job.required_skills),
            "certs: " + ", ".join(job.required_certifications),
            f"education: {job.education_level or ''}",
            f"experience: {job.minimum_experience} years",
        ]
        return " ".join(p for p in parts if p)

    def _profile_text(self, profile: CandidateProfile) -> str:
        parts = [
            profile.name or "",
            " ".join(profile.technical_skills),
            " ".join(profile.soft_skills),
            " ".join(f"{e.job_title} {e.company}" for e in profile.experience),
            " ".join(f"{e.degree} {e.university}" for e in profile.education),
            " ".join(p.name or "" for p in profile.projects),
            " ".join(profile.certifications),
        ]
        return " ".join(p for p in parts if p)

    def _skills_score(
        self, required: List[str], candidate: List[str], semantic_skills: float
    ) -> float:
        if not required:
            return max(0.4, min(1.0, 0.5 + 0.5 * semantic_skills))
        matched, _ = self._match_skills(required, candidate)
        overlap = len(matched) / len(required) if required else 0.0
        return float(max(0.0, min(1.0, 0.65 * overlap + 0.35 * max(0.0, semantic_skills))))

    def _experience_score(
        self, required_years: float, candidate_years: Optional[float], semantic: float
    ) -> float:
        years = float(candidate_years or 0.0)
        req = float(required_years or 0.0)
        if req <= 0:
            years_component = min(1.0, years / 8.0) if years else 0.35
        elif years >= req:
            years_component = min(1.0, 0.85 + 0.15 * min(1.0, (years - req) / max(req, 1)))
        else:
            years_component = max(0.0, years / req) * 0.85
        return float(max(0.0, min(1.0, 0.7 * years_component + 0.3 * max(0.0, semantic))))

    def _education_score(
        self, required_level: Optional[str], profile: CandidateProfile, semantic: float
    ) -> float:
        cand_level = 0
        blob = " ".join(
            f"{e.degree or ''} {e.field or ''}" for e in profile.education
        ).lower()
        for key, level in DEGREE_LEVELS.items():
            if key in blob:
                cand_level = max(cand_level, level)
        req_level = 0
        if required_level:
            low = required_level.lower()
            for key, level in DEGREE_LEVELS.items():
                if key in low:
                    req_level = max(req_level, level)
        if req_level <= 0:
            level_score = 0.45 + 0.11 * cand_level
        elif cand_level >= req_level:
            level_score = 1.0
        elif cand_level == 0:
            level_score = 0.2
        else:
            level_score = cand_level / req_level
        return float(max(0.0, min(1.0, 0.7 * level_score + 0.3 * max(0.0, semantic))))

    def _projects_score(
        self, required_skills: List[str], profile: CandidateProfile, semantic: float
    ) -> float:
        count_score = min(1.0, len(profile.projects) / 4.0) if profile.projects else 0.15
        project_names = " ".join(p.name or "" for p in profile.projects)
        tech = set()
        for p in profile.projects:
            tech.update(self._normalize_skill(t) for t in p.technologies)
            if p.name:
                tech.add(self._normalize_skill(p.name))
            if p.description:
                tech.add(self._normalize_skill(p.description[:80]))
        req = [self._normalize_skill(s) for s in required_skills if s]
        if req and tech:
            hits = sum(1 for r in req if any(r in t or t in r for t in tech if len(r) > 2))
            overlap = hits / len(req)
        else:
            overlap = 0.25 if project_names else 0.1
        return float(max(0.0, min(1.0, 0.35 * count_score + 0.35 * overlap + 0.3 * max(0.0, semantic))))

    def _certifications_score(self, required: List[str], candidate: List[str]) -> float:
        if not required:
            return min(1.0, 0.35 + 0.15 * len(candidate)) if candidate else 0.25
        req = {self._normalize_skill(c) for c in required}
        cand = {self._normalize_skill(c) for c in candidate}
        hits = sum(1 for r in req if any(r in c or c in r for c in cand))
        return float(hits / len(req)) if req else 0.3

    def _lexical_overlap(self, a: str, b: str) -> float:
        ta = set(normalize_for_matching(a).split())
        tb = set(normalize_for_matching(b).split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def _explain_skills(
        self, matched: List[str], missing: List[str], score: float
    ) -> str:
        return (
            f"Skills score {score:.2f}. Matched: {matched[:8] or ['none']}. "
            f"Missing: {missing[:8] or ['none']}."
        )
