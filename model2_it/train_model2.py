"""
train_model2.py

Train a LightGBM LambdaMART ranker (grouped by job_id) on train_features.csv,
select hyperparameters using validation_features.csv, and fit a skill-overlap
baseline for comparison. Test data is never used.

Improvements for top-1 accuracy:
  - Train on fine-grained relevance_score labels (0–100), not coarse 0–4 buckets
  - Validation tuning optimizes top-1 + NDCG jointly
  - ML + rule-based composite blend weight tuned on validation only

Usage (from model2_it/):
    python train_model2.py --features-dir features
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from itertools import product
from pathlib import Path
from typing import Dict, List, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd

from ranking_metrics import evaluate_ranking, top1_accuracy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("model2_train")

# Linear gain: label value equals relevance_score (0–100).
LABEL_GAIN = list(range(101))

SEARCH_GRID = {
    "num_leaves": [31, 63, 127],
    "learning_rate": [0.05, 0.1, 0.15],
    "n_estimators": [200, 400, 600],
    "min_child_samples": [5, 10, 20],
}


def _load_manifest(features_dir: Path) -> List[str]:
    manifest_path = features_dir / "feature_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing {manifest_path}; run prepare_model2_features.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest["feature_columns"]


def _sort_by_job(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["job_id", "candidate_id"]).reset_index(drop=True)


def _job_groups(df: pd.DataFrame) -> List[int]:
    return df.groupby("job_id", sort=False).size().tolist()


def _training_labels(df: pd.DataFrame) -> np.ndarray:
    """Fine-grained labels from relevance_score (target, not a feature)."""
    return df["relevance_score"].astype(float).round().astype(int).clip(0, 100).values


def _prepare_xy(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    x = df[feature_cols].astype(np.float32).values
    y = _training_labels(df).astype(np.float32)
    return x, y


def _rule_based_scores(df: pd.DataFrame) -> np.ndarray:
    if "rule_based_composite" in df.columns:
        return df["rule_based_composite"].astype(float).values
    return (
        df["required_skill_overlap"].astype(float) * 0.35
        + df.get("preferred_skill_overlap", 0).astype(float) * 0.15
        + df["experience_match_raw"].astype(float) * 0.15
        + df["project_relevance_raw"].astype(float) * 0.15
        + df["education_match_raw"].astype(float) * 0.10
        + df["certification_match_raw"].astype(float) * 0.05
        + df["graph_semantic_overlap"].astype(float) * 0.05
    ).values * 100.0


def _baseline_scores(df: pd.DataFrame) -> np.ndarray:
    return df["required_skill_overlap"].astype(float).values


def _normalize_within_job(df: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
    out = np.zeros(len(df), dtype=float)
    for i, (_, g) in enumerate(df.groupby("job_id", sort=False)):
        idx = g.index.to_numpy()
        s = scores[idx]
        smin, smax = s.min(), s.max()
        out[idx] = (s - smin) / (smax - smin) if smax > smin else np.zeros(len(s))
    return out


def _blend_scores(df: pd.DataFrame, ml_scores: np.ndarray, weight: float) -> np.ndarray:
    ml_norm = _normalize_within_job(df, ml_scores)
    rule_norm = _normalize_within_job(df, _rule_based_scores(df))
    return weight * ml_norm + (1.0 - weight) * rule_norm


def _tune_blend_weight(df: pd.DataFrame, ml_scores: np.ndarray) -> Tuple[float, float]:
    best_w = 0.0
    best_top1 = -1.0
    scored = df.copy()
    for w in np.linspace(0.0, 1.0, 21):
        scored["blend"] = _blend_scores(df, ml_scores, float(w))
        t1 = top1_accuracy(scored, "blend")
        if t1 > best_top1:
            best_top1 = t1
            best_w = float(w)
    return best_w, best_top1


def _val_objective(metrics: Dict[str, float]) -> float:
    """Prioritize picking the #1 candidate; keep NDCG high."""
    return 0.55 * metrics["top1_accuracy"] + 0.45 * metrics["ndcg_at_5"]


def _search_hyperparams(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feature_cols: List[str],
    seed: int,
) -> Tuple[Dict, float]:
    train_df = _sort_by_job(train_df)
    val_df = _sort_by_job(val_df)
    x_train, y_train = _prepare_xy(train_df, feature_cols)
    x_val, y_val = _prepare_xy(val_df, feature_cols)
    train_groups = _job_groups(train_df)
    val_groups = _job_groups(val_df)

    best_config: Dict | None = None
    best_obj = -1.0

    combos = list(product(
        SEARCH_GRID["num_leaves"],
        SEARCH_GRID["learning_rate"],
        SEARCH_GRID["n_estimators"],
        SEARCH_GRID["min_child_samples"],
    ))
    log.info("Hyperparameter search: %d configurations (label=relevance_score 0-100)", len(combos))

    for num_leaves, lr, n_est, min_child in combos:
        params = {
            "objective": "lambdarank",
            "metric": "ndcg",
            "ndcg_eval_at": [1, 5, 10],
            "label_gain": LABEL_GAIN,
            "learning_rate": lr,
            "num_leaves": num_leaves,
            "min_child_samples": min_child,
            "feature_pre_filter": False,
            "verbosity": -1,
            "seed": seed,
            "deterministic": True,
            "force_col_wise": True,
        }
        train_set = lgb.Dataset(x_train, label=y_train, group=train_groups)
        val_set = lgb.Dataset(x_val, label=y_val, group=val_groups, reference=train_set)

        model = lgb.train(
            params,
            train_set,
            num_boost_round=n_est,
            valid_sets=[val_set],
            valid_names=["validation"],
            callbacks=[lgb.early_stopping(stopping_rounds=40, verbose=False)],
        )

        val_pred = model.predict(x_val, num_iteration=model.best_iteration)
        val_scored = val_df.copy()
        val_scored["pred_score"] = val_pred
        metrics = evaluate_ranking(val_scored, "pred_score")
        obj = _val_objective(metrics)
        log.info(
            "Config leaves=%d lr=%.2f est=%d min_child=%d -> top1=%.4f ndcg5=%.4f obj=%.4f (iter=%d)",
            num_leaves, lr, n_est, min_child,
            metrics["top1_accuracy"], metrics["ndcg_at_5"], obj, model.best_iteration,
        )
        if obj > best_obj:
            best_obj = obj
            best_config = {
                "num_leaves": num_leaves,
                "learning_rate": lr,
                "n_estimators": n_est,
                "min_child_samples": min_child,
                "best_iteration": int(model.best_iteration),
                "validation_objective": round(obj, 4),
                "validation_metrics": metrics,
            }

    assert best_config is not None
    log.info("Best config: %s", best_config)
    return best_config, best_obj


def _train_final_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    feature_cols: List[str],
    config: Dict,
    seed: int,
) -> lgb.Booster:
    combined = _sort_by_job(pd.concat([train_df, val_df], ignore_index=True))
    x, y = _prepare_xy(combined, feature_cols)
    groups = _job_groups(combined)

    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "ndcg_eval_at": [1, 5, 10],
        "label_gain": LABEL_GAIN,
        "learning_rate": config["learning_rate"],
        "num_leaves": config["num_leaves"],
        "min_child_samples": config["min_child_samples"],
        "feature_pre_filter": False,
        "verbosity": -1,
        "seed": seed,
        "deterministic": True,
        "force_col_wise": True,
    }
    train_set = lgb.Dataset(x, label=y, group=groups)
    model = lgb.train(
        params,
        train_set,
        num_boost_round=config.get("best_iteration", config["n_estimators"]),
    )
    return model


def main():
    parser = argparse.ArgumentParser(description="Train Model 2 LightGBM LambdaMART ranker")
    parser.add_argument("--features-dir", type=str, default="features")
    parser.add_argument("--model-dir", type=str, default="models/best_model")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    features_dir = Path(args.features_dir)
    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    feature_cols = _load_manifest(features_dir)
    train_df = pd.read_csv(features_dir / "train_features.csv")
    val_df = pd.read_csv(features_dir / "validation_features.csv")

    log.info("Train rows=%d, validation rows=%d, features=%d", len(train_df), len(val_df), len(feature_cols))

    best_config, _ = _search_hyperparams(train_df, val_df, feature_cols, args.seed)

    hp = {
        "num_leaves": best_config["num_leaves"],
        "learning_rate": best_config["learning_rate"],
        "n_estimators": best_config["n_estimators"],
        "min_child_samples": best_config["min_child_samples"],
        "best_iteration": best_config["best_iteration"],
    }
    model = _train_final_model(train_df, val_df, feature_cols, hp, args.seed)
    model_path = model_dir / "lgbm_ranker.txt"
    model.save_model(str(model_path))
    log.info("Wrote %s", model_path)

    val_sorted = _sort_by_job(val_df)
    x_val, _ = _prepare_xy(val_sorted, feature_cols)
    val_sorted = val_sorted.copy()
    val_sorted["ml_score"] = model.predict(x_val)
    blend_w, val_top1_blend = _tune_blend_weight(val_sorted, val_sorted["ml_score"].values)
    log.info("Blend weight (ML): %.2f -> validation top1=%.4f", blend_w, val_top1_blend)

    val_sorted["final_score"] = _blend_scores(
        val_sorted, val_sorted["ml_score"].values, blend_w
    )
    val_ml = evaluate_ranking(val_sorted, "ml_score")
    val_final = evaluate_ranking(val_sorted, "final_score")
    val_baseline = evaluate_ranking(
        val_sorted.assign(baseline_score=_baseline_scores(val_sorted)),
        "baseline_score",
    )

    config_out = {
        "model_type": "lightgbm_lambdarank",
        "training_label": "relevance_score_rounded_0_100",
        "label_gain": "linear_0_to_100",
        "feature_columns": feature_cols,
        "hyperparameters": hp,
        "ml_blend_weight": round(blend_w, 4),
        "rule_blend_weight": round(1.0 - blend_w, 4),
        "validation_objective": best_config["validation_objective"],
        "validation_metrics_ml": val_ml,
        "validation_metrics_blended": val_final,
        "validation_metrics_baseline": val_baseline,
        "baseline_type": "required_skill_overlap",
    }
    config_path = model_dir / "best_model_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_out, f, indent=2)
    log.info("Wrote %s", config_path)
    log.info("Validation ML: %s", val_ml)
    log.info("Validation blended: %s", val_final)
    log.info("Training complete. Test set was NOT used.")


if __name__ == "__main__":
    main()
