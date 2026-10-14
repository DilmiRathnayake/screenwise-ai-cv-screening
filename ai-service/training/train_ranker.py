"""
Train, calibrate, and evaluate IT candidate ranking (Model 02).

Pipeline:
  1. Build pair features from train split
  2. Train LightGBM classifier on relevance_label
  3. Calibrate semantic fusion, ML blend, and shortlist threshold on val
  4. Evaluate held-out test metrics (real — no fabrication)

Usage (from ai-service/):
  python -m training.preprocess_it_datasets
  python -m training.train_ranker --eval-split test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.configs.ranking_weights import INDUSTRY_WEIGHTS, SHORTLIST_THRESHOLD
from app.configs.settings import get_settings
from app.repositories.ranker_repository import RankerRepository
from app.schemas.models import (
    CandidateProfile,
    EducationEntry,
    JobRequirements,
    ProjectEntry,
    RankCandidateInput,
    RankRequest,
)
from app.services.ranking_features import FEATURE_NAMES, build_features
from app.services.ranking_service import RankingService
from app.utils.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def _parse_skills(value) -> list[str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    text = str(value)
    parts = [p.strip() for p in text.replace("|", ",").replace(";", ",").split(",")]
    return [p for p in parts if p and p.lower() != "nan"]


def _load_baseline_metrics(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "ai_screening" in data:
            return {"ai_screening": data["ai_screening"], "resume_data": data.get("resume_data")}
        return data
    except Exception:
        return None


def row_to_profile(row: dict) -> CandidateProfile:
    skills = _parse_skills(row.get("technical_skills"))
    certs = _parse_skills(row.get("certifications"))
    projects_raw = _parse_skills(row.get("projects"))
    projects = [ProjectEntry(name=p, technologies=skills[:3]) for p in projects_raw[:8]]
    years = None
    try:
        years = float(row.get("years_experience") or 0)
    except (TypeError, ValueError):
        years = None

    comm = 0.5
    try:
        comm = float(row.get("score_communication") or 50) / 100.0
    except (TypeError, ValueError):
        pass

    raw = " ".join(
        [
            str(row.get("name") or ""),
            " ".join(skills),
            str(row.get("education_degree") or ""),
            " ".join(projects_raw),
            " ".join(certs),
            f"experience {years or 0} years",
        ]
    )

    return CandidateProfile(
        name=str(row.get("name") or ""),
        email=str(row.get("email") or ""),
        phone=str(row.get("phone") or ""),
        technical_skills=skills,
        soft_skills=_parse_skills(row.get("soft_skills")),
        years_of_experience=years,
        education=[EducationEntry(degree=str(row.get("education_degree") or ""))],
        projects=projects,
        certifications=certs,
        communication_score=max(0.0, min(1.0, comm)),
        raw_text=raw[:4000],
    )


def job_row_to_requirements(row: dict) -> JobRequirements:
    req_skills = _parse_skills(row.get("required_skills"))
    pref = _parse_skills(row.get("preferred_skills"))
    all_skills = list(dict.fromkeys(req_skills + pref))
    min_exp = 0.0
    try:
        min_exp = float(row.get("min_experience_years") or 0)
    except (TypeError, ValueError):
        pass

    return JobRequirements(
        title=str(row.get("title") or "IT Role"),
        description=str(row.get("description") or ""),
        required_skills=all_skills or req_skills or ["Python"],
        minimum_experience=min_exp,
        education_level="Bachelor",
        industry="it",
    )


def _load_split_ids(csv_path: Path) -> set[str]:
    if not csv_path.exists():
        return set()
    df = pd.read_csv(csv_path)
    return set(df["candidate_id"].astype(str))


def _binary_metrics(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict:
    y_pred = (y_score >= threshold).astype(int)
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / max(len(y_true), 1)
    return {
        "threshold": round(threshold, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }


def _ndcg_at_k(relevance: List[float], scores: List[float], k: int = 5) -> float:
    idx = np.argsort(scores)[::-1][:k]
    rel = np.asarray(relevance)[idx]
    discounts = 1.0 / np.log2(np.arange(2, len(rel) + 2))
    dcg = float(np.sum(rel * discounts))
    ideal = np.sort(relevance)[::-1][:k]
    idcg = float(np.sum(ideal * discounts[: len(ideal)]))
    return dcg / idcg if idcg > 0 else 0.0


def _mrr(relevance_groups: List[List[int]], score_groups: List[List[float]]) -> float:
    rr = []
    for rels, scores in zip(relevance_groups, score_groups):
        order = np.argsort(scores)[::-1]
        for rank, idx in enumerate(order, start=1):
            if rels[idx] == 1:
                rr.append(1.0 / rank)
                break
        else:
            rr.append(0.0)
    return float(np.mean(rr)) if rr else 0.0


def build_pair_features(
    service: RankingService,
    matches_path: Path,
    jobs_path: Path,
    candidates_path: Path,
    candidate_ids: Optional[set[str]] = None,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    matches = pd.read_csv(matches_path)
    jobs = pd.read_csv(jobs_path)
    candidates = pd.read_csv(candidates_path)
    jobs.columns = [c.strip() for c in jobs.columns]
    candidates.columns = [c.strip() for c in candidates.columns]

    if candidate_ids:
        matches = matches[matches["candidate_id"].astype(str).isin(candidate_ids)]

    cand_lookup = {r["candidate_id"]: r for _, r in candidates.iterrows()}
    job_lookup = {r["job_id"]: r for _, r in jobs.iterrows()}

    rows: List[np.ndarray] = []
    labels: List[int] = []
    pair_keys: List[str] = []

    for _, mrow in matches.iterrows():
        cid = mrow["candidate_id"]
        job_id = mrow["job_id"]
        cand_row = cand_lookup.get(cid)
        job_row = job_lookup.get(job_id)
        if cand_row is None or job_row is None:
            continue

        profile = row_to_profile(cand_row.to_dict())
        job = job_row_to_requirements(job_row.to_dict())
        job_blob = service._job_text(job)
        weights = service._resolve_weights(job)
        raw = profile.raw_text or service._profile_text(profile)
        comp = service._score_components(profile, raw, job, job_blob, weights)
        feat = build_features(
            profile, job, comp["criterion_raw"], comp["semantic"], comp["rule_final"]
        )
        rows.append(feat)
        labels.append(int(mrow.get("relevance_label") or 0))
        pair_keys.append(f"{job_id}:{cid}")

    if not rows:
        return np.zeros((0, len(FEATURE_NAMES)), dtype=np.float32), np.array([]), []

    return np.vstack(rows), np.asarray(labels, dtype=np.int32), pair_keys


def train_lgbm(X: np.ndarray, y: np.ndarray):
    import lightgbm as lgb

    pos = int((y == 1).sum())
    neg = int((y == 0).sum())
    scale = neg / max(pos, 1)
    model = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        subsample=0.85,
        colsample_bytree=0.85,
        class_weight="balanced",
        scale_pos_weight=scale,
        random_state=42,
        verbose=-1,
    )
    model.fit(X, y, feature_name=FEATURE_NAMES)
    return model


def evaluate_candidates_csv(
    service: RankingService,
    csv_path: Path,
    threshold: float,
) -> dict:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    y_true: List[int] = []
    y_score: List[float] = []
    gold_scores: List[float] = []

    for _, row in df.iterrows():
        profile = row_to_profile(row.to_dict())
        job = JobRequirements(
            title="IT Software Engineer",
            description=f"IT role requiring {', '.join(profile.technical_skills[:6])}",
            required_skills=profile.technical_skills[:8] or ["Python", "JavaScript"],
            minimum_experience=float(profile.years_of_experience or 0) * 0.7,
            education_level=str(row.get("education_degree") or "Bachelor"),
            industry="it",
        )
        resp = service.rank(
            RankRequest(job=job, candidates=[RankCandidateInput(profile=profile)])
        )
        score = resp.top_candidates[0].candidate_score
        y_score.append(score)
        y_true.append(int(row.get("label") or 0))
        try:
            gold_scores.append(float(row.get("overall_score") or 0) / 100.0)
        except (TypeError, ValueError):
            gold_scores.append(0.0)

    y_true_a = np.asarray(y_true)
    y_score_a = np.asarray(y_score)
    gold_a = np.asarray(gold_scores)

    metrics = _binary_metrics(y_true_a, y_score_a, threshold)
    spearman = float(pd.Series(y_score_a).corr(pd.Series(gold_a), method="spearman"))
    metrics.update(
        {
            "dataset": csv_path.name,
            "n_samples": len(df),
            "spearman_vs_overall_score": round(spearman, 4) if spearman == spearman else None,
            "mean_pred": round(float(np.mean(y_score_a)), 4),
            "mean_gold": round(float(np.mean(gold_a)), 4),
        }
    )
    return metrics


def evaluate_pair_matches(
    service: RankingService,
    matches_path: Path,
    jobs_path: Path,
    candidates_path: Path,
    candidate_ids: Optional[set[str]] = None,
    threshold: Optional[float] = None,
) -> dict:
    matches = pd.read_csv(matches_path)
    jobs = pd.read_csv(jobs_path)
    candidates = pd.read_csv(candidates_path)
    jobs.columns = [c.strip() for c in jobs.columns]
    candidates.columns = [c.strip() for c in candidates.columns]

    if candidate_ids:
        matches = matches[matches["candidate_id"].astype(str).isin(candidate_ids)]

    cand_lookup = {r["candidate_id"]: r for _, r in candidates.iterrows()}
    job_lookup = {r["job_id"]: r for _, r in jobs.iterrows()}

    y_true: List[int] = []
    y_score: List[float] = []
    ndcg_scores: List[float] = []
    rel_groups: List[List[int]] = []
    score_groups: List[List[float]] = []

    for job_id, group in matches.groupby("job_id"):
        job_row = job_lookup.get(job_id)
        if job_row is None:
            continue
        job = job_row_to_requirements(job_row.to_dict())
        rank_inputs: List[RankCandidateInput] = []
        group_rels: List[int] = []

        for _, mrow in group.iterrows():
            cid = mrow["candidate_id"]
            cand_row = cand_lookup.get(cid)
            if cand_row is None:
                continue
            profile = row_to_profile(cand_row.to_dict())
            rank_inputs.append(RankCandidateInput(candidate_id=str(cid), profile=profile))
            group_rels.append(int(mrow.get("relevance_label") or 0))

        if len(rank_inputs) < 2:
            continue

        resp = service.rank(RankRequest(job=job, candidates=rank_inputs))
        by_id = {c.candidate_id: c.candidate_score for c in resp.top_candidates}
        group_scores: List[float] = []

        for _, mrow in group.iterrows():
            cid = str(mrow["candidate_id"])
            if cid not in by_id:
                continue
            y_true.append(int(mrow.get("relevance_label") or 0))
            y_score.append(by_id[cid])
            group_scores.append(by_id[cid])

        rel_groups.append(group_rels)
        score_groups.append(group_scores)
        if group_rels and group_scores and len(group_rels) == len(group_scores):
            ndcg_scores.append(_ndcg_at_k(group_rels, group_scores, k=min(5, len(group_rels))))

    y_true_a = np.asarray(y_true)
    y_score_a = np.asarray(y_score)
    thr = threshold if threshold is not None else (
        float(np.median(y_score_a)) if len(y_score_a) else 0.5
    )
    binary = _binary_metrics(y_true_a, y_score_a, thr) if len(y_true_a) else {}

    k = 5
    if len(y_score_a):
        top_k_idx = np.argsort(y_score_a)[::-1][:k]
        prec_at_k = float(y_true_a[top_k_idx].sum() / k)
        total_pos = max(int(y_true_a.sum()), 1)
        rec_at_k = float(y_true_a[top_k_idx].sum() / total_pos)
    else:
        prec_at_k = rec_at_k = 0.0

    return {
        "dataset": "it_candidate_job_matches.csv",
        "n_pairs": len(y_true_a),
        "n_job_groups": len(rel_groups),
        "precision_at_5": round(prec_at_k, 4),
        "recall_at_5": round(rec_at_k, 4),
        "mrr": round(_mrr(rel_groups, score_groups), 4),
        "ndcg_at_5": round(float(np.mean(ndcg_scores)), 4) if ndcg_scores else 0.0,
        **{k: v for k, v in binary.items() if k != "threshold"},
        "threshold_used": round(thr, 4),
    }


def _score_val_candidates(service: RankingService, val_csv: Path) -> Tuple[np.ndarray, np.ndarray]:
    val_df = pd.read_csv(val_csv)
    y_true: List[int] = []
    y_score: List[float] = []
    for _, row in val_df.iterrows():
        profile = row_to_profile(row.to_dict())
        job = JobRequirements(
            title="IT Software Engineer",
            description=f"IT role requiring {', '.join(profile.technical_skills[:6])}",
            required_skills=profile.technical_skills[:8] or ["Python"],
            minimum_experience=float(profile.years_of_experience or 0) * 0.7,
            industry="it",
        )
        resp = service.rank(
            RankRequest(job=job, candidates=[RankCandidateInput(profile=profile)])
        )
        y_score.append(resp.top_candidates[0].candidate_score)
        y_true.append(int(row.get("label") or 0))
    return np.asarray(y_true), np.asarray(y_score)


def _fuse_score(rule: float, semantic: float, ml_prob: Optional[float], sem_w: float, ml_w: float) -> float:
    base = rule
    if ml_prob is not None and ml_w > 0:
        base = (1.0 - ml_w) * rule + ml_w * max(0.0, min(1.0, ml_prob))
    return (1.0 - sem_w) * base + sem_w * max(0.0, min(1.0, semantic))


def _precompute_val_pair_scores(
    service: RankingService,
    settings,
    val_ids: set[str],
    lgbm_model,
) -> Tuple[
    List[List[int]],
    List[List[float]],
    List[List[float]],
    List[List[Optional[float]]],
    np.ndarray,
    List[float],
    List[float],
    List[Optional[float]],
]:
    matches = pd.read_csv(settings.it_candidate_job_matches_csv)
    jobs = pd.read_csv(settings.it_job_descriptions_csv)
    candidates = pd.read_csv(settings.it_candidates_full_csv)
    matches = matches[matches["candidate_id"].astype(str).isin(val_ids)]
    cand_lookup = {r["candidate_id"]: r for _, r in candidates.iterrows()}
    job_lookup = {r["job_id"]: r for _, r in jobs.iterrows()}

    rel_groups: List[List[int]] = []
    rule_groups: List[List[float]] = []
    sem_groups: List[List[float]] = []
    ml_groups: List[List[Optional[float]]] = []
    flat_labels: List[int] = []

    for job_id, group in matches.groupby("job_id"):
        job_row = job_lookup.get(job_id)
        if job_row is None:
            continue
        job = job_row_to_requirements(job_row.to_dict())
        job_blob = service._job_text(job)
        weights = service._resolve_weights(job)

        group_rels: List[int] = []
        group_rule: List[float] = []
        group_sem: List[float] = []
        group_ml: List[Optional[float]] = []

        for _, mrow in group.iterrows():
            cand_row = cand_lookup.get(mrow["candidate_id"])
            if cand_row is None:
                continue
            profile = row_to_profile(cand_row.to_dict())
            raw = profile.raw_text or service._profile_text(profile)
            comp = service._score_components(profile, raw, job, job_blob, weights)
            ml_prob = None
            if lgbm_model is not None:
                feat = build_features(
                    profile, job, comp["criterion_raw"], comp["semantic"], comp["rule_final"]
                )
                proba = lgbm_model.predict_proba(feat.reshape(1, -1))[0]
                ml_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
            group_rels.append(int(mrow.get("relevance_label") or 0))
            group_rule.append(comp["rule_final"])
            group_sem.append(comp["semantic"])
            group_ml.append(ml_prob)
            flat_labels.append(int(mrow.get("relevance_label") or 0))

        if len(group_rels) >= 2:
            rel_groups.append(group_rels)
            rule_groups.append(group_rule)
            sem_groups.append(group_sem)
            ml_groups.append(group_ml)

    val_df = pd.read_csv(settings.it_candidates_val_csv)
    cand_y_true: List[int] = []
    cand_rule: List[float] = []
    cand_sem: List[float] = []
    cand_ml: List[Optional[float]] = []
    for _, row in val_df.iterrows():
        profile = row_to_profile(row.to_dict())
        job = JobRequirements(
            title="IT Software Engineer",
            description=f"IT role requiring {', '.join(profile.technical_skills[:6])}",
            required_skills=profile.technical_skills[:8] or ["Python"],
            minimum_experience=float(profile.years_of_experience or 0) * 0.7,
            industry="it",
        )
        raw = profile.raw_text or service._profile_text(profile)
        jb = service._job_text(job)
        w = service._resolve_weights(job)
        comp = service._score_components(profile, raw, job, jb, w)
        ml_prob = None
        if lgbm_model is not None:
            feat = build_features(profile, job, comp["criterion_raw"], comp["semantic"], comp["rule_final"])
            proba = lgbm_model.predict_proba(feat.reshape(1, -1))[0]
            ml_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        cand_y_true.append(int(row.get("label") or 0))
        cand_rule.append(comp["rule_final"])
        cand_sem.append(comp["semantic"])
        cand_ml.append(ml_prob)

    return (
        rel_groups,
        rule_groups,
        sem_groups,
        ml_groups,
        np.asarray(cand_y_true),
        cand_rule,
        cand_sem,
        cand_ml,
    )


def calibrate_on_validation(
    service: RankingService,
    settings,
    lgbm_model=None,
) -> dict:
    """Grid-search semantic fusion, ML blend, and shortlist threshold on val split."""
    val_ids = _load_split_ids(settings.it_candidates_val_csv)
    best = {
        "semantic_fusion_weight": 0.12,
        "ml_blend_weight": 0.35,
        "shortlist_threshold": SHORTLIST_THRESHOLD,
        "score": -1.0,
    }

    semantic_grid = [0.08, 0.10, 0.12, 0.15, 0.18, 0.22]
    ml_blend_grid = [0.0, 0.25, 0.35, 0.45, 0.55] if lgbm_model is not None else [0.0]
    threshold_grid = [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]

    logger.info("Precomputing validation scores for fast calibration...")
    (
        rel_groups,
        rule_groups,
        sem_groups,
        ml_groups,
        cand_y_true,
        cand_rule,
        cand_sem,
        cand_ml,
    ) = _precompute_val_pair_scores(service, settings, val_ids, lgbm_model)

    for sem_w in semantic_grid:
        for ml_w in ml_blend_grid:
            score_groups: List[List[float]] = []
            ndcg_scores: List[float] = []
            for rels, rules, sems, mls in zip(rel_groups, rule_groups, sem_groups, ml_groups):
                fused = [
                    _fuse_score(r, s, m, sem_w, ml_w) for r, s, m in zip(rules, sems, mls)
                ]
                score_groups.append(fused)
                if len(rels) >= 2:
                    ndcg_scores.append(_ndcg_at_k(rels, fused, k=min(5, len(rels))))

            pair_val = {
                "ndcg_at_5": float(np.mean(ndcg_scores)) if ndcg_scores else 0.0,
                "mrr": _mrr(rel_groups, score_groups),
                "precision_at_5": 0.0,
            }
            flat_scores = [s for grp in score_groups for s in grp]
            flat_labels = [l for grp in rel_groups for l in grp]
            if flat_scores:
                top_k = np.argsort(flat_scores)[::-1][:5]
                pair_val["precision_at_5"] = float(np.asarray(flat_labels)[top_k].sum() / 5)

            cand_scores = [
                _fuse_score(r, s, m, sem_w, ml_w)
                for r, s, m in zip(cand_rule, cand_sem, cand_ml)
            ]
            for thr in threshold_grid:
                bin_m = _binary_metrics(cand_y_true, np.asarray(cand_scores), thr)
                composite = (
                    0.40 * pair_val["ndcg_at_5"]
                    + 0.30 * pair_val["mrr"]
                    + 0.20 * bin_m.get("f1", 0.0)
                    + 0.10 * pair_val["precision_at_5"]
                )
                if composite > best["score"]:
                    best = {
                        "semantic_fusion_weight": sem_w,
                        "ml_blend_weight": ml_w,
                        "shortlist_threshold": thr,
                        "score": round(composite, 4),
                        "val_pair_ndcg_at_5": round(pair_val["ndcg_at_5"], 4),
                        "val_pair_mrr": round(pair_val["mrr"], 4),
                        "val_binary_f1": bin_m.get("f1"),
                    }

    logger.info("Calibration best: %s", best)
    return best


def train_and_evaluate(eval_split: str = "test", skip_embeddings: bool = False) -> dict:
    settings = get_settings()
    settings.ranking_model_path.mkdir(parents=True, exist_ok=True)
    metrics_path = settings.ranking_model_path / "metrics.json"
    baseline = _load_baseline_metrics(metrics_path)

    if skip_embeddings:
        class _FailEmb:
            is_loaded = False

            def section_similarity(self, *a, **k):
                raise RuntimeError("embeddings skipped")

            def encode(self, *a, **k):
                raise RuntimeError("embeddings skipped")

        base_service = RankingService(embeddings=_FailEmb())  # type: ignore
    else:
        base_service = RankingService()
        try:
            base_service.embeddings.encode(["warmup"])
        except Exception as exc:
            logger.warning("Embeddings unavailable: %s", exc)

    train_ids = _load_split_ids(settings.it_candidates_train_csv)
    val_ids = _load_split_ids(settings.it_candidates_val_csv)
    test_ids = _load_split_ids(settings.it_candidates_test_csv)

    logger.info("Building train pair features (%d train candidates)...", len(train_ids))
    X_train, y_train, _ = build_pair_features(
        base_service,
        settings.it_candidate_job_matches_csv,
        settings.it_job_descriptions_csv,
        settings.it_candidates_full_csv,
        candidate_ids=train_ids,
    )

    lgbm_model = None
    if len(X_train) >= 50 and y_train.sum() > 0:
        logger.info("Training LightGBM on %d pairs (pos=%d)...", len(y_train), int(y_train.sum()))
        lgbm_model = train_lgbm(X_train, y_train)
        import joblib

        model_path = settings.ranking_model_path / "lgbm_ranker.pkl"
        joblib.dump(lgbm_model, model_path)
        logger.info("Saved LightGBM to %s", model_path)
    else:
        logger.warning("Insufficient train pairs for LightGBM — skipping ML ranker")

    ranker = RankerRepository(settings.ranking_model_path)
    service = RankingService(
        embeddings=base_service.embeddings,
        ranker=ranker,
    )

    logger.info("Calibrating on validation set...")
    calibration = calibrate_on_validation(service, settings, lgbm_model=lgbm_model)
    calibration["it_weights"] = INDUSTRY_WEIGHTS["it"]
    calibration["feature_names"] = FEATURE_NAMES
    cal_path = settings.ranking_model_path / "calibration.json"
    cal_path.write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    ranker = RankerRepository(settings.ranking_model_path)
    service = RankingService(embeddings=base_service.embeddings, ranker=ranker)

    threshold = float(calibration["shortlist_threshold"])
    eval_csv = (
        settings.it_candidates_test_csv
        if eval_split == "test"
        else settings.it_candidates_val_csv
    )
    if not eval_csv.exists():
        raise FileNotFoundError(f"Ranking eval CSV not found: {eval_csv}")

    logger.info("Evaluating candidates on %s ...", eval_csv.name)
    candidate_metrics = evaluate_candidates_csv(service, eval_csv, threshold)

    eval_ids = test_ids if eval_split == "test" else val_ids
    logger.info("Evaluating candidate-job pairs (%s candidates)...", eval_split)
    pair_metrics = evaluate_pair_matches(
        service,
        settings.it_candidate_job_matches_csv,
        settings.it_job_descriptions_csv,
        settings.it_candidates_full_csv,
        candidate_ids=eval_ids if eval_ids else None,
        threshold=threshold,
    )

    lgbm_info = {}
    if lgbm_model is not None:
        try:
            import joblib

            lgbm_info = {
                "train_pairs": len(y_train),
                "train_positives": int(y_train.sum()),
                "feature_importance_top5": dict(
                    sorted(
                        zip(FEATURE_NAMES, lgbm_model.feature_importances_.tolist()),
                        key=lambda x: x[1],
                        reverse=True,
                    )[:5]
                ),
            }
        except Exception:
            pass

    results = {
        "models": "weighted_multi_criteria + sentence_transformers + lightgbm",
        "dataset": "ScreenWise_IT_Ranking",
        "eval_split": eval_split,
        "baseline": baseline,
        "calibration": calibration,
        "it_weights": INDUSTRY_WEIGHTS["it"],
        "lgbm": lgbm_info,
        "candidate_eval": candidate_metrics,
        "pair_eval_test": pair_metrics,
    }

    metrics_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    (settings.ranking_model_path / "industry_weights.json").write_text(
        json.dumps(INDUSTRY_WEIGHTS, indent=2), encoding="utf-8"
    )
    logger.info("Wrote ranking metrics to %s", metrics_path)
    return results


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate IT candidate ranking")
    parser.add_argument(
        "--eval-split",
        choices=("test", "val"),
        default="test",
        help="Held-out split for final metrics",
    )
    parser.add_argument("--skip-embeddings", action="store_true")
    args = parser.parse_args()
    train_and_evaluate(eval_split=args.eval_split, skip_embeddings=args.skip_embeddings)


if __name__ == "__main__":
    main()
