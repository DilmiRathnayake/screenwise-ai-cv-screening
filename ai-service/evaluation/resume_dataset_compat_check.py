"""Compatibility (robustness) check: run the EXISTING extraction pipeline over a sample of the resume dataset.

This is software testing, not machine-learning evaluation: the dataset's annotations are all one generic
'SKILL: <word>' type and include non-skill words, so they are NOT used as ground truth here. Nothing is trained,
no model file is written, and only aggregate numbers are reported (no resume text is printed or saved).

Prerequisite: python datasets/prepare_resume_dataset.py   (creates datasets/processed/resume_json_index.csv)
Usage (from ai-service/):  python -m evaluation.resume_dataset_compat_check --sample 100
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import statistics
import sys
import time
from pathlib import Path

AI = Path(__file__).resolve().parents[1]
ROOT = AI.parent
sys.path.insert(0, str(AI))
os.environ.setdefault("GEMINI_API_KEY", "")  # no cloud calls from this check
os.environ.setdefault("PINECONE_API_KEY", "")

DATASETS = ROOT / "datasets"
JSON_DIR = DATASETS / "ResumesJsonAnnotated" / "ResumesJsonAnnotated"
PDF_DIR = DATASETS / "ResumesPDF" / "ResumesPDF"
INDEX = DATASETS / "processed" / "resume_json_index.csv"
OUT = DATASETS / "processed" / "resume_compat_check.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--all-categories", action="store_true", help="sample from all unique records, not only it_candidate")
    args = ap.parse_args()

    from app.services.extraction_service import ExtractionService
    from app.services.ocr_service import OCRService

    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    pool = [
        r for r in rows
        if r["empty_text"] == "0" and not r["duplicate_of_cv_number"]
        and (args.all_categories or r["it_candidate"] == "1")
    ]
    random.Random(args.seed).shuffle(pool)
    sample = pool[: args.sample]

    svc, ocr = ExtractionService(), OCRService()
    res = {"sample_size": len(sample), "pool_size": len(pool), "seed": args.seed,
           "ner_model_loaded": svc.ner_loaded, "scope": "all unique records" if args.all_categories else "it_candidate unique records"}

    # 1) JSON text -> extraction pipeline
    fail = no_skills = no_edu = no_exp = 0
    times, n_skills = [], []
    for r in sample:
        text = json.loads((JSON_DIR / r["json_file"]).read_bytes().decode("utf-8"))["text"]
        t0 = time.perf_counter()
        try:
            p = svc.extract_from_text(text)
        except Exception:
            fail += 1
            continue
        times.append(time.perf_counter() - t0)
        n_skills.append(len(p.technical_skills))
        no_skills += not p.technical_skills
        no_edu += not p.education
        no_exp += not p.experience
    ok = len(sample) - fail
    res["json_text_extraction"] = {
        "crashed": fail, "completed": ok,
        "no_technical_skills_found": no_skills, "no_education_found": no_edu, "no_experience_found": no_exp,
        "median_seconds": round(statistics.median(times), 4) if times else None,
        "median_skills_per_cv": statistics.median(n_skills) if n_skills else None,
    }

    # 2) paired PDF -> text extraction (PyMuPDF; OCR/Gemini fallbacks are not triggered here)
    pdf_ok = pdf_short = pdf_fail = pdf_missing = 0
    methods: dict[str, int] = {}
    for r in sample:
        if not r["pdf_file"]:
            pdf_missing += 1
            continue
        try:
            text, method = ocr.extract_text(r["pdf_file"], (PDF_DIR / r["pdf_file"]).read_bytes())
        except Exception:
            pdf_fail += 1
            continue
        methods[method] = methods.get(method, 0) + 1
        if len(text.strip()) < 200:
            pdf_short += 1
        else:
            pdf_ok += 1
    res["pdf_text_extraction"] = {"readable_text": pdf_ok, "very_short_or_empty_text": pdf_short,
                                  "failed": pdf_fail, "no_pdf_for_record": pdf_missing, "methods": methods}

    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
