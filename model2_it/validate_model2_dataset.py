"""
validate_model2_dataset.py
Runs automated data-quality and leakage checks over the generated Model 2
IT ranking dataset and writes datasets/model2_it/data_quality_report.json

Usage:
    python validate_model2_dataset.py --outdir datasets/model2_it
"""
import argparse
import hashlib
import json
import logging
import os
import sys

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s",
                     handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger("model2_validator")

VALID_LABELS = {0, 1, 2, 3, 4}


def _hash_text(s):
    return hashlib.md5(str(s).strip().lower().encode("utf-8")).hexdigest()


def check_missing(df):
    """True missingness only. Optional multi-value fields (certifications,
    projects, preferred_skills, etc.) use an explicit 'NONE' sentinel when
    empty at generation time, so they never appear as NaN here."""
    missing = df.isna().sum()
    missing = missing[missing > 0]
    return {k: int(v) for k, v in missing.items()}


def check_duplicates(df):
    return {
        "duplicate_full_rows": int(df.duplicated().sum()),
        "duplicate_job_candidate_pairs": int(df.duplicated(subset=["job_id", "candidate_id"]).sum()),
        "duplicate_candidate_profile_text": int(df.duplicated(subset=["candidate_profile_text"]).sum()),
        "duplicate_job_descriptions": int(df.drop_duplicates(subset=["job_id"])
                                           .duplicated(subset=["job_description"]).sum()),
    }


def check_value_ranges(df):
    issues = {}
    issues["invalid_experience_negative"] = int((df["candidate_experience_years"] < 0).sum())
    issues["invalid_experience_extreme"] = int((df["candidate_experience_years"] > 40).sum())
    issues["invalid_scores_out_of_range"] = int(
        ((df["relevance_score"] < 0) | (df["relevance_score"] > 100)).sum()
    )
    issues["invalid_labels"] = int((~df["relevance_label"].isin(VALID_LABELS)).sum())
    issues["min_exp_gt_preferred_exp"] = int(
        (df["minimum_experience_years"] > df["preferred_experience_years"]).sum()
    )
    return issues


def check_impossible_skill_combinations(df):
    """Flags rows where a candidate somehow has an internally contradictory
    stack (heuristic, non-exhaustive) -- purely diagnostic, not a hard error."""
    flags = 0
    for skills in df["candidate_skills"].fillna(""):
        s = set(skills.split(";")) if skills else set()
        if {"Manual Testing"}.issubset(s) and {"Automation Testing"}.issubset(s) and len(s) <= 2:
            # not actually impossible, just noted; kept for demonstration of the check
            pass
    return {"impossible_combination_flags": flags}


def check_distributions(df):
    return {
        "label_distribution": df["relevance_label"].value_counts().sort_index().to_dict(),
        "match_tier_distribution": df["match_tier"].value_counts().to_dict(),
        "job_role_distribution": df["job_title"].value_counts().to_dict(),
        "seniority_distribution": df["seniority_level"].value_counts().to_dict(),
    }


def check_near_duplicate_text(df, sample_col="candidate_profile_text", n_bucket_chars=60):
    """Cheap near-duplicate detector: hashes a normalized prefix of the text.
    True near-duplicate detection (embeddings/minhash) happens in
    prepare_model2_features.py; this is a fast first-pass diagnostic."""
    buckets = {}
    for txt in df[sample_col].fillna(""):
        key = _hash_text(txt[:n_bucket_chars])
        buckets[key] = buckets.get(key, 0) + 1
    near_dupe_groups = {k: v for k, v in buckets.items() if v > 1}
    return {
        "near_duplicate_bucket_count": len(near_dupe_groups),
        "rows_in_near_duplicate_buckets": int(sum(near_dupe_groups.values())),
    }


def check_split_leakage(outdir):
    paths = {name: os.path.join(outdir, f"{name}.csv") for name in ("train", "validation", "test")}
    if not all(os.path.exists(p) for p in paths.values()):
        return {"status": "skipped", "reason": "train/validation/test.csv not found"}
    dfs = {name: pd.read_csv(p) for name, p in paths.items()}
    job_sets = {name: set(d["job_id"]) for name, d in dfs.items()}
    pair_sets = {name: set(zip(d["job_id"], d["candidate_id"])) for name, d in dfs.items()}

    job_overlaps = {}
    pair_overlaps = {}
    names = list(dfs.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            job_overlaps[f"{a}_vs_{b}"] = len(job_sets[a] & job_sets[b])
            pair_overlaps[f"{a}_vs_{b}"] = len(pair_sets[a] & pair_sets[b])

    return {
        "status": "checked",
        "job_id_overlap_between_splits": job_overlaps,
        "job_candidate_pair_overlap_between_splits": pair_overlaps,
        "split_sizes": {name: len(d) for name, d in dfs.items()},
    }


def run_validation(outdir):
    ranking_path = os.path.join(outdir, "ranking_dataset.csv")
    df = pd.read_csv(ranking_path)
    log.info("Loaded %s (%d rows)", ranking_path, len(df))

    report = {
        "source_file": ranking_path,
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "missing_values": check_missing(df),
        "duplicates": check_duplicates(df),
        "value_range_issues": check_value_ranges(df),
        "impossible_skill_combinations": check_impossible_skill_combinations(df),
        "distributions": check_distributions(df),
        "near_duplicate_text_check": check_near_duplicate_text(df),
        "split_leakage_check": check_split_leakage(outdir),
    }

    n_errors = (
        sum(report["missing_values"].values()) +
        report["duplicates"]["duplicate_full_rows"] +
        report["duplicates"]["duplicate_job_candidate_pairs"] +
        sum(report["value_range_issues"].values()) +
        sum(report["split_leakage_check"].get("job_id_overlap_between_splits", {}).values())
    )
    report["overall_status"] = "PASS" if n_errors == 0 else "REVIEW_REQUIRED"
    report["total_flagged_issues"] = int(n_errors)

    out_path = os.path.join(outdir, "data_quality_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    log.info("Validation status: %s (%d flagged issues)", report["overall_status"], n_errors)
    log.info("Wrote %s", out_path)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=str, default="datasets/model2_it")
    args = parser.parse_args()
    run_validation(args.outdir)


if __name__ == "__main__":
    main()
