"""
Shared ranking evaluation metrics for Model 2 (IT Candidate Ranking).

Used by train_model2.py (validation tuning) and evaluate_model2.py (test eval).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
from scipy.stats import kendalltau, spearmanr


def _dcg(relevances: np.ndarray, k: int) -> float:
    rel = np.asarray(relevances, dtype=float)[:k]
    if rel.size == 0:
        return 0.0
    discounts = 1.0 / np.log2(np.arange(2, rel.size + 2))
    return float(np.sum(rel * discounts))


def ndcg_at_k(relevance: Sequence[float], scores: Sequence[float], k: int = 5) -> float:
    rel = np.asarray(relevance, dtype=float)
    scr = np.asarray(scores, dtype=float)
    if rel.size == 0:
        return 0.0
    order = np.argsort(scr)[::-1]
    dcg = _dcg(rel[order], k)
    ideal = _dcg(np.sort(rel)[::-1], k)
    return dcg / ideal if ideal > 0 else 0.0


def mrr(relevance_groups: List[List[float]], score_groups: List[List[float]]) -> float:
    rr: List[float] = []
    for rels, scores in zip(relevance_groups, score_groups):
        order = np.argsort(scores)[::-1]
        found = 0.0
        for rank, idx in enumerate(order, start=1):
            if rels[idx] > 0:
                found = 1.0 / rank
                break
        rr.append(found)
    return float(np.mean(rr)) if rr else 0.0


def precision_recall_at_k(
    relevance_groups: List[List[float]],
    score_groups: List[List[float]],
    k: int = 5,
    relevance_threshold: float = 3.0,
) -> Tuple[float, float]:
    precisions: List[float] = []
    recalls: List[float] = []
    for rels, scores in zip(relevance_groups, score_groups):
        rel_bin = [1 if r >= relevance_threshold else 0 for r in rels]
        total_relevant = sum(rel_bin)
        if total_relevant == 0:
            continue
        order = np.argsort(scores)[::-1][:k]
        hits = sum(rel_bin[i] for i in order)
        precisions.append(hits / min(k, len(rels)))
        recalls.append(hits / total_relevant)
    if not precisions:
        return 0.0, 0.0
    return float(np.mean(precisions)), float(np.mean(recalls))


def group_by_job(
    df,
    job_col: str,
    relevance_col: str,
    score_col: str,
) -> Tuple[List[List[float]], List[List[float]]]:
    rel_groups: List[List[float]] = []
    score_groups: List[List[float]] = []
    for _, g in df.sort_values(job_col).groupby(job_col, sort=False):
        rel_groups.append(g[relevance_col].astype(float).tolist())
        score_groups.append(g[score_col].astype(float).tolist())
    return rel_groups, score_groups


def correlation_metrics(y_true: Iterable[float], y_pred: Iterable[float]) -> Dict[str, float]:
    yt = np.asarray(list(y_true), dtype=float)
    yp = np.asarray(list(y_pred), dtype=float)
    if yt.size < 2 or np.std(yt) == 0 or np.std(yp) == 0:
        return {"spearman": 0.0, "kendall_tau": 0.0}
    sp = spearmanr(yt, yp).statistic
    kt = kendalltau(yt, yp).statistic
    return {
        "spearman": round(float(sp), 4) if sp == sp else 0.0,
        "kendall_tau": round(float(kt), 4) if kt == kt else 0.0,
    }


def top1_accuracy(
    df,
    score_col: str,
    gold_col: str = "relevance_score",
    job_col: str = "job_id",
) -> float:
    """Fraction of jobs where the highest-scoring candidate matches gold best candidate."""
    hits = 0
    jobs = 0
    for _, g in df.groupby(job_col, sort=False):
        jobs += 1
        gold_id = g.loc[g[gold_col].astype(float).idxmax(), "candidate_id"]
        pred_id = g.loc[g[score_col].astype(float).idxmax(), "candidate_id"]
        if gold_id == pred_id:
            hits += 1
    return hits / jobs if jobs else 0.0


def evaluate_ranking(
    df,
    score_col: str,
    relevance_col: str = "relevance_label",
    job_col: str = "job_id",
    relevance_threshold: float = 3.0,
    gold_score_col: str = "relevance_score",
) -> Dict[str, float]:
    rel_groups, score_groups = group_by_job(df, job_col, relevance_col, score_col)
    ndcg5 = float(np.mean([ndcg_at_k(r, s, 5) for r, s in zip(rel_groups, score_groups)]))
    ndcg10 = float(np.mean([ndcg_at_k(r, s, 10) for r, s in zip(rel_groups, score_groups)]))
    p5, r5 = precision_recall_at_k(
        rel_groups, score_groups, k=5, relevance_threshold=relevance_threshold
    )
    corr = correlation_metrics(df[relevance_col], df[score_col])
    top1 = top1_accuracy(df, score_col, gold_col=gold_score_col, job_col=job_col)
    return {
        "ndcg_at_5": round(ndcg5, 4),
        "ndcg_at_10": round(ndcg10, 4),
        "mrr": round(mrr(rel_groups, score_groups), 4),
        "precision_at_5": round(p5, 4),
        "recall_at_5": round(r5, 4),
        "top1_accuracy": round(top1, 4),
        **corr,
    }
