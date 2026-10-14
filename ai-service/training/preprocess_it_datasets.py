"""
Preprocess ScreenWise IT datasets into cleaned copies under datasets/processed/.

Does NOT modify original dataset files.

Usage (from ai-service/):
  python -m training.preprocess_it_datasets
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.configs.settings import get_settings
from app.utils.logging_config import get_logger, setup_logging
from training.data_loader import _dedupe_overlaps, _filter_aligned_entities

setup_logging()
logger = get_logger(__name__)

IT_NER_LABELS = {"NAME", "EMAIL", "SKILL", "DEGREE", "CERTIFICATION"}


def _load_ner_json(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    raise ValueError(f"Expected JSON array in {path}")


def _clean_ner_record(record: Dict[str, Any]) -> Dict[str, Any] | None:
    text = (record.get("text") or "").strip()
    if not text:
        return None

    entities: List[Tuple[int, int, str]] = []
    for ent in record.get("entities") or []:
        if len(ent) != 3:
            continue
        start, end, label = int(ent[0]), int(ent[1]), str(ent[2]).upper()
        if label not in IT_NER_LABELS:
            continue
        if start < 0 or end > len(text) or start >= end:
            continue
        span = text[start:end]
        if not span.strip():
            continue
        entities.append((start, end, label))

    entities = _dedupe_overlaps(entities)
    entities = _filter_aligned_entities(text, entities)
    if not entities:
        return None

    return {
        "text": text,
        "entities": [[s, e, l] for s, e, l in entities],
    }


def preprocess_ner(ner_dir: Path, out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stats: Dict[str, Any] = {"splits": {}, "label_counts": {}}
    label_counter: Counter = Counter()

    for split in ("full", "train", "val", "test"):
        src_name = f"it_ner_{split}.json"
        src = ner_dir / src_name
        if not src.exists():
            logger.warning("NER split missing: %s", src)
            continue

        raw = _load_ner_json(src)
        cleaned: List[Dict[str, Any]] = []
        dropped = 0
        for rec in raw:
            c = _clean_ner_record(rec)
            if c:
                cleaned.append(c)
                for _, _, lbl in c["entities"]:
                    label_counter[lbl] += 1
            else:
                dropped += 1

        out_path = out_dir / src_name
        out_path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
        stats["splits"][split] = {
            "source": str(src),
            "input_records": len(raw),
            "output_records": len(cleaned),
            "dropped": dropped,
        }
        logger.info("NER %s: %s -> %s records (%s dropped)", split, len(raw), len(cleaned), dropped)

    stats["label_counts"] = dict(label_counter)
    return stats


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _dedupe_rows(rows: List[Dict[str, str]], key: str) -> Tuple[List[Dict[str, str]], int]:
    seen: set = set()
    kept: List[Dict[str, str]] = []
    removed = 0
    for row in rows:
        k = row.get(key, "")
        if k in seen:
            removed += 1
            continue
        seen.add(k)
        kept.append(row)
    return kept, removed


def preprocess_ranking(rank_dir: Path, out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stats: Dict[str, Any] = {"files": {}}

    for fname in (
        "it_candidates_full.csv",
        "it_train.csv",
        "it_val.csv",
        "it_test.csv",
        "it_job_descriptions.csv",
        "it_candidate_job_matches.csv",
    ):
        src = rank_dir / fname
        if not src.exists():
            logger.warning("Ranking file missing: %s", src)
            continue

        rows = _read_csv(src)
        fieldnames = list(rows[0].keys()) if rows else []
        dropped_dup = 0
        dropped_email = 0

        if fname.startswith("it_candidates") or fname.startswith("it_train") or fname.startswith("it_val") or fname.startswith("it_test"):
            # Drop duplicate candidate_id rows
            seen_ids: set = set()
            filtered: List[Dict[str, str]] = []
            for row in rows:
                cid = row.get("candidate_id", "")
                if cid in seen_ids:
                    dropped_dup += 1
                    continue
                seen_ids.add(cid)
                # Validate numeric scores
                for col in (
                    "score_skills",
                    "score_experience",
                    "score_education",
                    "score_communication",
                    "score_projects",
                    "score_certifications",
                    "overall_score",
                ):
                    if col in row and row[col]:
                        try:
                            val = float(row[col])
                            row[col] = str(max(0.0, min(100.0, val)))
                        except ValueError:
                            pass
                filtered.append(row)
            rows = filtered

        if fname == "it_candidates_full.csv":
            # Flag duplicate emails — keep first occurrence only
            seen_emails: set = set()
            email_filtered: List[Dict[str, str]] = []
            for row in rows:
                email = (row.get("email") or "").strip().lower()
                if email and email in seen_emails:
                    dropped_email += 1
                    continue
                if email:
                    seen_emails.add(email)
                email_filtered.append(row)
            rows = email_filtered

        out_path = out_dir / fname
        _write_csv(out_path, rows, fieldnames)
        stats["files"][fname] = {
            "source": str(src),
            "records": len(rows),
            "dropped_duplicate_ids": dropped_dup,
            "dropped_duplicate_emails": dropped_email,
        }
        logger.info("Ranking %s: %s records written", fname, len(rows))

    return stats


def main() -> None:
    settings = get_settings()
    processed_root = settings.processed_datasets_dir
    ner_out = processed_root / "ner"
    rank_out = processed_root / "ranking"

    logger.info("Preprocessing IT NER from %s", settings.it_ner_datasets_dir)
    ner_stats = preprocess_ner(settings.it_ner_datasets_dir, ner_out)

    logger.info("Preprocessing IT ranking from %s", settings.it_ranking_datasets_dir)
    rank_stats = preprocess_ranking(settings.it_ranking_datasets_dir, rank_out)

    report = {
        "ner": ner_stats,
        "ranking": rank_stats,
        "processed_root": str(processed_root),
    }
    report_path = processed_root / "dataset_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Wrote dataset report to %s", report_path)


if __name__ == "__main__":
    main()
