"""Audit and index the annotated resume dataset (JSON + PDF) WITHOUT modifying it.

Reads  : datasets/ResumesJsonAnnotated/ResumesJsonAnnotated/*.json  (+ datasets/ResumesPDF/ResumesPDF/*.pdf names)
Writes : datasets/processed/resume_json_index.csv        one row per JSON record (no resume text is copied)
         datasets/processed/resume_dataset_summary.json  aggregate counts only

The dataset has NO category labels, so an "IT" subset cannot be taken from a label. `it_candidate` is a
transparent heuristic: the text contains at least --min-it-skills DISTINCT skills from the project's own IT
taxonomy (model2_it/taxonomy.py). It is a convenience flag, not ground truth.

Usage (from the project root):  python datasets/prepare_resume_dataset.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JSON_DIR = HERE / "ResumesJsonAnnotated" / "ResumesJsonAnnotated"
PDF_DIR = HERE / "ResumesPDF" / "ResumesPDF"
OUT_DIR = HERE / "processed"


def load_it_skills() -> list[str]:
    sys.path.insert(0, str(ROOT / "model2_it"))
    from taxonomy import ALL_SKILLS  # project IT skill taxonomy

    return [s for s in ALL_SKILLS if len(s) > 2]  # skip 1-2 letter names (C, R, Go): too ambiguous as words


def compile_patterns(skills: list[str]) -> list[tuple[str, re.Pattern]]:
    return [
        (s, re.compile(rf"(?<![A-Za-z0-9]){re.escape(s.lower())}(?![A-Za-z0-9])"))
        for s in skills
    ]


def cv_number(name: str) -> int:
    m = re.search(r"\((\d+)\)", name)
    return int(m.group(1)) if m else -1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-it-skills", type=int, default=5)
    args = ap.parse_args()

    if not JSON_DIR.is_dir():
        sys.exit(f"JSON folder not found: {JSON_DIR}")
    OUT_DIR.mkdir(exist_ok=True)

    patterns = compile_patterns(load_it_skills())
    json_files = sorted(JSON_DIR.glob("*.json"), key=lambda p: cv_number(p.name))
    pdf_numbers = {cv_number(p.name) for p in PDF_DIR.glob("*.pdf")} if PDF_DIR.is_dir() else set()

    rows, first_seen = [], {}
    stats = Counter()
    label_types: Counter = Counter()
    for f in json_files:
        stats["json_files"] += 1
        try:
            rec = json.loads(f.read_bytes().decode("utf-8"))
        except Exception:
            stats["unparseable"] += 1
            continue
        text = rec.get("text") or ""
        ann = rec.get("annotations") or []
        n = cv_number(f.name)

        spans, bad = [], 0
        for a in ann:
            s, e, lab = a[0], a[1], a[2]
            label_types[str(lab).split(":")[0]] += 1
            if not (isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(text)):
                bad += 1
            else:
                spans.append((s, e))
        spans.sort()
        overlaps = sum(1 for a, b in zip(spans, spans[1:]) if b[0] < a[1])

        key = hashlib.md5(text.strip().lower().encode("utf-8", "surrogatepass")).hexdigest()
        dup_of = first_seen.get(key, "")
        if not dup_of and text.strip():
            first_seen[key] = n
        low = text.lower()
        hits = sum(1 for _, p in patterns if p.search(low))

        empty = not text.strip()
        stats["empty_text"] += empty
        stats["duplicate_text"] += bool(dup_of)
        stats["invalid_offsets_records"] += bad > 0
        stats["records_with_overlapping_spans"] += overlaps > 0
        stats["zero_annotation_records"] += len(ann) == 0
        stats["spans_total"] += len(ann)
        stats["overlapping_span_pairs"] += overlaps
        stats["has_lone_surrogate"] += any(0xD800 <= ord(c) <= 0xDFFF for c in text)
        it = hits >= args.min_it_skills and not empty
        stats["it_candidate_all"] += it
        stats["it_candidate_unique"] += it and not dup_of

        rows.append(
            {
                "cv_number": n,
                "json_file": f.name,
                "pdf_file": f"cv ({n}).pdf" if n in pdf_numbers else "",
                "text_chars": len(text),
                "annotation_spans": len(ann),
                "overlapping_span_pairs": overlaps,
                "empty_text": int(empty),
                "duplicate_of_cv_number": dup_of,
                "it_skill_hits": hits,
                "it_candidate": int(it),
            }
        )

    with open(OUT_DIR / "resume_json_index.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    summary = {
        "json_dir": str(JSON_DIR.relative_to(ROOT)),
        "pdf_files": len(pdf_numbers),
        "pdf_without_json": len(pdf_numbers - {r["cv_number"] for r in rows}),
        "min_it_skills_rule": args.min_it_skills,
        "label_types": dict(label_types),
        **dict(stats),
    }
    (OUT_DIR / "resume_dataset_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
