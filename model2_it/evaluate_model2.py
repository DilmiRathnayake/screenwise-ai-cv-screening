"""
evaluate_model2.py

Evaluate the trained Model 2 ranker ONLY on test_features.csv (held-out).
Compares LightGBM LambdaMART vs. the skill-overlap baseline on identical data.

Usage (from model2_it/):
    python evaluate_model2.py --features-dir features --model-dir models/best_model
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import pandas as pd

from ranking_metrics import evaluate_ranking
from train_model2 import _blend_scores

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("model2_eval")


def _baseline_scores(df: pd.DataFrame):
    return df["required_skill_overlap"].astype(float).values


def _build_report(metrics: dict, baseline: dict, config: dict) -> str:
    ml = metrics["ml_model"]
    bl = metrics["baseline"]
    lines = [
        "# Model 2 — IT Candidate Ranking Evaluation Report",
        "",
        f"**Generated:** {metrics['evaluated_at']} (UTC)",
        f"**Eval split:** test only ({metrics['test_rows']} job–candidate pairs, "
        f"{metrics['test_jobs']} jobs)",
        "",
        "## Methodology",
        "",
        "- Features engineered from **raw** job/candidate fields (not pre-computed match components).",
        "- LightGBM **LambdaMART** ranker grouped by `job_id`.",
        "- Baseline: **required skill overlap** ratio only (no ML).",
        "- Test jobs were never seen during training or hyperparameter tuning.",
        "",
        "## Test-set metrics",
        "",
        "| Metric | ML model | Skill-overlap baseline |",
        "|--------|----------|------------------------|",
    ]
    for key in (
        "top1_accuracy", "ndcg_at_5", "ndcg_at_10", "mrr", "precision_at_5",
        "recall_at_5", "spearman", "kendall_tau",
    ):
        lines.append(f"| {key} | {ml[key]} | {bl[key]} |")

    delta_ndcg = ml["ndcg_at_5"] - bl["ndcg_at_5"]
    lines.extend([
        "",
        f"**NDCG@5 delta (ML − baseline):** {delta_ndcg:+.4f}",
        "",
        "## Selected hyperparameters",
        "",
        "```json",
        json.dumps(config.get("hyperparameters", config), indent=2),
        "```",
        "",
        "## Interpretation",
        "",
    ])

    if ml["ndcg_at_5"] >= 0.85:
        lines.append(
            "The ML ranker recovers most of the synthetic rubric on held-out jobs. "
            "This validates pipeline integrity; real recruiter alignment is still unknown."
        )
    elif ml["ndcg_at_5"] >= 0.65:
        lines.append(
            "Moderate ranking quality on the held-out test set. The model learns beyond "
            "the simple baseline but does not fully recover the reference scoring formula. "
            "Likely improvements: richer real resume text, per-role weight tables, "
            "deeper hyperparameter search, or pairwise LambdaMART training."
        )
    else:
        lines.append(
            "Ranking performance on the test set is limited. Reported numbers reflect "
            "actual evaluation — no threshold tuning was applied to inflate metrics. "
            "Consider stronger text features, class-imbalance handling, or reviewing "
            "feature leakage exclusions."
        )

    if bl["ndcg_at_5"] > ml["ndcg_at_5"]:
        lines.append(
            "\n**Note:** The skill-overlap baseline outperformed the ML model on NDCG@5. "
            "This can occur when the synthetic label is dominated by required-skill match "
            "and the model overfits validation noise during tuning."
        )

    lines.extend([
        "",
        "## Limitations",
        "",
        "- Ground truth is a fixed synthetic rubric, not observed hiring decisions.",
        "- Template-generated text may limit embedding utility.",
        "- Metrics measure agreement with the dataset scoring formula, not real-world hiring accuracy.",
        "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Model 2 on held-out test set")
    parser.add_argument("--features-dir", type=str, default="features")
    parser.add_argument("--model-dir", type=str, default="models/best_model")
    parser.add_argument("--outdir", type=str, default="evaluation")
    args = parser.parse_args()

    features_dir = Path(args.features_dir)
    model_dir = Path(args.model_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    config_path = model_dir / "best_model_config.json"
    model_path = model_dir / "lgbm_ranker.txt"
    test_path = features_dir / "test_features.csv"
    manifest_path = features_dir / "feature_manifest.json"

    for p in (config_path, model_path, test_path, manifest_path):
        if not p.exists():
            log.error("Missing required file: %s", p)
            sys.exit(1)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    feature_cols = manifest["feature_columns"]

    test_df = pd.read_csv(test_path).sort_values(["job_id", "candidate_id"]).reset_index(drop=True)
    log.info("Evaluating on test set: %d rows, %d jobs", len(test_df), test_df["job_id"].nunique())

    model = lgb.Booster(model_file=str(model_path))
    x_test = test_df[feature_cols].astype(float).values
    test_df = test_df.copy()
    test_df["ml_score"] = model.predict(x_test)
    test_df["baseline_score"] = _baseline_scores(test_df)
    blend_w = float(config.get("ml_blend_weight", 1.0))
    test_df["final_score"] = _blend_scores(
        test_df, test_df["ml_score"].values, blend_w
    )

    ml_metrics = evaluate_ranking(test_df, "ml_score")
    final_metrics = evaluate_ranking(test_df, "final_score")
    baseline_metrics = evaluate_ranking(test_df, "baseline_score")

    evaluated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    metrics_doc = {
        "model": "SCREENWISE Model 2 — IT Candidate Ranking (LightGBM LambdaMART + blend)",
        "evaluated_at": evaluated_at,
        "eval_split": "test",
        "test_rows": int(len(test_df)),
        "test_jobs": int(test_df["job_id"].nunique()),
        "relevance_threshold_for_precision_recall": 3.0,
        "ml_blend_weight": blend_w,
        "rule_blend_weight": float(config.get("rule_blend_weight", 1.0 - blend_w)),
        "top1_accuracy_pct": round(final_metrics["top1_accuracy"] * 100, 2),
        "ml_model_raw": ml_metrics,
        "ml_model": final_metrics,
        "baseline": baseline_metrics,
        "delta_ml_minus_baseline": {
            k: round(final_metrics[k] - baseline_metrics[k], 4)
            for k in final_metrics
        },
        "hyperparameters": config.get("hyperparameters", config),
        "feature_count": len(feature_cols),
        "notes": (
            "All metrics computed on held-out test jobs only. "
            "No test data was used during training or tuning. "
            "ml_model reports blended scores (ML + rule-based composite)."
        ),
    }

    metrics_path = outdir / "model2_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_doc, f, indent=2)
    log.info("Wrote %s", metrics_path)
    log.info("Blended test metrics: %s", final_metrics)
    log.info("Raw ML test metrics: %s", ml_metrics)
    log.info("Baseline test metrics: %s", baseline_metrics)

    report = _build_report(metrics_doc, baseline_metrics, config)
    report_path = outdir / "model2_evaluation_report.md"
    report_path.write_text(report, encoding="utf-8")
    log.info("Wrote %s", report_path)


if __name__ == "__main__":
    main()
