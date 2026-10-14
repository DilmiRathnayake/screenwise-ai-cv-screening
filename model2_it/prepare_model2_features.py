"""
prepare_model2_features.py

Engineer Model 2 ranking features from RAW job/candidate fields (not the
pre-computed match components), add cached sentence-transformer embeddings,
and write features/{train,validation,test}_features.csv.

Usage (from model2_it/):
    python prepare_model2_features.py --datadir datasets/model2_it
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd

from taxonomy import EDUCATION_RANK, related_skills

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("model2_features")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Same weights as dataset scoring (computed from raw fields — not CSV leakage columns).
COMPONENT_WEIGHTS = {
    "required_skill": 0.35,
    "preferred_skill": 0.15,
    "experience": 0.15,
    "project": 0.15,
    "education": 0.10,
    "certification": 0.05,
    "semantic": 0.05,
}

METADATA_COLS = {
    "job_id", "candidate_id", "relevance_label", "relevance_score",
    "rank_within_job", "match_tier", "candidate_archetype", "data_source",
}
LEAKAGE_COLS = {
    "required_skill_match", "preferred_skill_match", "experience_match",
    "project_relevance", "education_match", "certification_match", "semantic_similarity",
}
RAW_TEXT_COLS = {
    "job_description", "candidate_profile_text", "candidate_experience_description",
    "candidate_project_description", "job_title", "seniority_level",
    "required_skills", "preferred_skills", "candidate_skills", "candidate_education",
    "required_education", "preferred_education", "required_certifications",
    "preferred_certifications", "candidate_certifications", "required_project_types",
    "candidate_projects", "technical_requirements", "responsibilities",
    "soft_skill_requirements", "candidate_job_titles",
}


def _parse_list(value) -> List[str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    text = str(value).strip()
    if not text or text.upper() == "NONE":
        return []
    return [p.strip() for p in text.split(";") if p.strip() and p.strip().upper() != "NONE"]


def _experience_match(min_exp: float, pref_exp: float, cand_exp: float) -> Tuple[float, float, float]:
    pref_exp = max(pref_exp, min_exp)
    diff_min = cand_exp - min_exp
    diff_pref = cand_exp - pref_exp
    if cand_exp < min_exp:
        score = max(0.0, 1.0 - (min_exp - cand_exp) / max(1.0, min_exp + 1.0))
    elif cand_exp <= pref_exp:
        denom = max(1.0, pref_exp - min_exp)
        score = 0.8 + 0.2 * ((cand_exp - min_exp) / denom)
    else:
        over = cand_exp - pref_exp
        score = max(0.5, 1.0 - 0.05 * over)
    return round(score, 4), round(diff_min, 4), round(diff_pref, 4)


def _education_match(required_edu: str, candidate_edu: str) -> Tuple[float, float]:
    req_rank = EDUCATION_RANK.get(required_edu, 3)
    cand_rank = EDUCATION_RANK.get(candidate_edu, 3)
    if cand_rank >= req_rank:
        score = 1.0
    else:
        score = max(0.0, 1.0 - 0.25 * (req_rank - cand_rank))
    return round(score, 4), round(cand_rank - req_rank, 4)


def _project_relevance(required_types: Set[str], candidate_projects: Set[str]) -> float:
    if required_types:
        return round(len(required_types & candidate_projects) / len(required_types), 4)
    if candidate_projects:
        return round(min(1.0, 0.3 + 0.2 * len(candidate_projects)), 4)
    return 0.0


def _certification_match(
    req_certs: Set[str], pref_certs: Set[str], cand_certs: Set[str]
) -> Tuple[float, int]:
    if req_certs:
        score = len(req_certs & cand_certs) / len(req_certs)
    elif pref_certs:
        score = 0.5 + 0.5 * (len(pref_certs & cand_certs) / len(pref_certs))
    else:
        score = 0.5 if cand_certs else 0.4
    matched = len((req_certs | pref_certs) & cand_certs)
    return round(score, 4), matched


def _graph_semantic_overlap(job_terms: Set[str], cand_terms: Set[str]) -> float:
    expanded = set(cand_terms)
    for skill in cand_terms:
        expanded.update(related_skills(skill))
    if not job_terms:
        return 0.0
    return round(len(job_terms & expanded) / len(job_terms), 4)


def engineer_row_features(row: pd.Series) -> Dict[str, float]:
    req = set(_parse_list(row.get("required_skills")))
    pref = set(_parse_list(row.get("preferred_skills")))
    have = set(_parse_list(row.get("candidate_skills")))
    req_projects = set(_parse_list(row.get("required_project_types")))
    cand_projects = set(_parse_list(row.get("candidate_projects")))
    req_certs = set(_parse_list(row.get("required_certifications")))
    pref_certs = set(_parse_list(row.get("preferred_certifications")))
    cand_certs = set(_parse_list(row.get("candidate_certifications")))

    req_overlap = (len(req & have) / len(req)) if req else 1.0
    pref_overlap = (len(pref & have) / len(pref)) if pref else 1.0
    missing_req = len(req - have)
    missing_pref = len(pref - have)
    missing_req_ratio = (missing_req / len(req)) if req else 0.0
    missing_pref_ratio = (missing_pref / len(pref)) if pref else 0.0

    min_exp = float(row.get("minimum_experience_years") or 0)
    pref_exp = float(row.get("preferred_experience_years") or min_exp)
    cand_exp = float(row.get("candidate_experience_years") or 0)
    exp_match, exp_diff_min, exp_diff_pref = _experience_match(min_exp, pref_exp, cand_exp)

    edu_match, edu_rank_diff = _education_match(
        str(row.get("required_education", "")),
        str(row.get("candidate_education", "")),
    )
    proj_rel = _project_relevance(req_projects, cand_projects)
    cert_match, cert_count = _certification_match(req_certs, pref_certs, cand_certs)
    graph_sem = _graph_semantic_overlap(req | pref, have)

    skill_jaccard = (
        len((req | pref) & have) / len(req | pref | have)
        if (req | pref | have)
        else 0.0
    )

    feats = {
        "required_skill_overlap": round(req_overlap, 4),
        "preferred_skill_overlap": round(pref_overlap, 4),
        "missing_required_skills": float(missing_req),
        "missing_preferred_skills": float(missing_pref),
        "missing_required_ratio": round(missing_req_ratio, 4),
        "missing_preferred_ratio": round(missing_pref_ratio, 4),
        "skill_jaccard": round(skill_jaccard, 4),
        "experience_years": cand_exp,
        "minimum_experience_years": min_exp,
        "preferred_experience_years": pref_exp,
        "experience_diff_min": exp_diff_min,
        "experience_diff_pref": exp_diff_pref,
        "experience_match_raw": exp_match,
        "meets_minimum_experience": float(cand_exp >= min_exp),
        "education_match_raw": edu_match,
        "education_rank_diff": edu_rank_diff,
        "project_relevance_raw": proj_rel,
        "candidate_project_count": float(len(cand_projects)),
        "required_project_count": float(len(req_projects)),
        "certification_match_raw": cert_match,
        "candidate_cert_count": float(len(cand_certs)),
        "certifications_matched": float(cert_count),
        "graph_semantic_overlap": graph_sem,
        "req_x_exp": round(req_overlap * exp_match, 4),
        "req_x_edu": round(req_overlap * edu_match, 4),
        "req_x_proj": round(req_overlap * proj_rel, 4),
        "pref_x_exp": round(pref_overlap * exp_match, 4),
        "exp_x_edu": round(exp_match * edu_match, 4),
        "rule_based_composite": round(
            100.0 * (
                req_overlap * COMPONENT_WEIGHTS["required_skill"]
                + pref_overlap * COMPONENT_WEIGHTS["preferred_skill"]
                + exp_match * COMPONENT_WEIGHTS["experience"]
                + proj_rel * COMPONENT_WEIGHTS["project"]
                + edu_match * COMPONENT_WEIGHTS["education"]
                + cert_match * COMPONENT_WEIGHTS["certification"]
                + graph_sem * COMPONENT_WEIGHTS["semantic"]
            ),
            4,
        ),
    }
    return feats


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_embedding_cache(cache_dir: Path) -> Dict[str, np.ndarray]:
    cache_file = cache_dir / "embedding_cache.npz"
    if not cache_file.exists():
        return {}
    data = np.load(cache_file, allow_pickle=True)
    return {str(k): data[k] for k in data.files}


def _save_embedding_cache(cache_dir: Path, cache: Dict[str, np.ndarray]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "embedding_cache.npz"
    if cache:
        np.savez_compressed(cache_file, **cache)
    log.info("Embedding cache: %d vectors -> %s", len(cache), cache_file)


def _build_embeddings(
    texts: List[str],
    cache_dir: Path,
    model_name: str,
    batch_size: int,
) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    cache = _load_embedding_cache(cache_dir)
    unique_texts = list(dict.fromkeys(texts))
    missing = [t for t in unique_texts if _text_hash(t) not in cache]

    if missing:
        log.info("Encoding %d new texts with %s (batch=%d)", len(missing), model_name, batch_size)
        model = SentenceTransformer(model_name)
        for start in range(0, len(missing), batch_size):
            batch = missing[start : start + batch_size]
            vectors = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
            for text, vec in zip(batch, vectors):
                cache[_text_hash(text)] = np.asarray(vec, dtype=np.float32)
        _save_embedding_cache(cache_dir, cache)
    else:
        log.info("All %d texts found in embedding cache", len(unique_texts))

    return np.vstack([cache[_text_hash(t)] for t in texts])


def prepare_split(
    df: pd.DataFrame,
    cache_dir: Path,
    model_name: str,
    batch_size: int,
) -> pd.DataFrame:
    log.info("Engineering tabular features for %d rows", len(df))
    engineered = pd.DataFrame([engineer_row_features(row) for _, row in df.iterrows()])
    pair_texts = (
        df["job_description"].fillna("").astype(str)
        + " [SEP] "
        + df["candidate_profile_text"].fillna("").astype(str)
    ).tolist()
    embeddings = _build_embeddings(pair_texts, cache_dir, model_name, batch_size)
    emb_cols = {f"emb_{i}": embeddings[:, i] for i in range(embeddings.shape[1])}
    emb_df = pd.DataFrame(emb_cols)

    meta_cols = [c for c in METADATA_COLS if c in df.columns]
    out = pd.concat([df[meta_cols].reset_index(drop=True), engineered, emb_df], axis=1)
    return out


def main():
    parser = argparse.ArgumentParser(description="Prepare Model 2 IT ranking features")
    parser.add_argument("--datadir", type=str, default="datasets/model2_it")
    parser.add_argument("--outdir", type=str, default="features")
    parser.add_argument("--cache-dir", type=str, default="cache/embeddings")
    parser.add_argument("--embedding-model", type=str, default=EMBEDDING_MODEL)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    datadir = Path(args.datadir)
    outdir = Path(args.outdir)
    cache_dir = Path(args.cache_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    splits = ("train", "validation", "test")
    feature_cols: List[str] = []

    for split in splits:
        path = datadir / f"{split}.csv" if split != "validation" else datadir / "validation.csv"
        if not path.exists() and split == "validation":
            path = datadir / "val.csv"
        if not path.exists():
            log.error("Missing split file: %s", path)
            sys.exit(1)
        df = pd.read_csv(path)
        log.info("Processing %s (%d rows)", split, len(df))
        features_df = prepare_split(df, cache_dir, args.embedding_model, args.batch_size)
        out_path = outdir / f"{split}_features.csv"
        features_df.to_csv(out_path, index=False)
        log.info("Wrote %s (%d rows, %d cols)", out_path, len(features_df), features_df.shape[1])

        if not feature_cols:
            feature_cols = [
                c for c in features_df.columns
                if c not in METADATA_COLS and c not in LEAKAGE_COLS and c not in RAW_TEXT_COLS
            ]

    manifest = {
        "embedding_model": args.embedding_model,
        "embedding_dim": EMBEDDING_DIM,
        "feature_columns": feature_cols,
        "metadata_columns": sorted(METADATA_COLS),
        "excluded_leakage_columns": sorted(LEAKAGE_COLS),
        "engineered_from": "raw job/candidate fields (not pre-computed match components)",
    }
    manifest_path = outdir / "feature_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log.info("Wrote %s (%d features)", manifest_path, len(feature_cols))


if __name__ == "__main__":
    main()
