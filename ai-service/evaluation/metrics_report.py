"""Evaluation helpers for dissertation metrics reporting."""

from __future__ import annotations

import json
from pathlib import Path


def load_metrics(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_phase1(ai_service_root: Path) -> dict:
    extraction = load_metrics(ai_service_root / "models" / "extraction" / "metrics.json")
    ranking = load_metrics(ai_service_root / "models" / "ranking" / "metrics.json")
    return {
        "extraction": extraction,
        "ranking": ranking,
    }
