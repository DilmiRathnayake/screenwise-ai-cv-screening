"""Convert Entity Recognition JSON (+ optional weak labels) into spaCy training data."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

LABEL_MAP = {
    "Name": "NAME",
    "Email Address": "EMAIL",
    "Skills": "SKILL",
    "Degree": "DEGREE",
    "College Name": "COLLEGE",
    "Companies worked at": "COMPANY",
    "Designation": "DESIGNATION",
    "Location": "LOCATION",
    "Graduation Year": "GRAD_YEAR",
    "Years of Experience": "YOE",
}

IT_NER_LABELS = ("NAME", "EMAIL", "SKILL", "DEGREE", "CERTIFICATION")


def load_ner_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def annotations_to_spacy_example(record: Dict[str, Any]) -> Optional[Tuple[str, Dict]]:
    text = record.get("content") or ""
    if not text.strip():
        return None

    entities: List[Tuple[int, int, str]] = []
    for ann in record.get("annotation") or []:
        labels = ann.get("label") or []
        if not labels:
            continue
        raw_label = labels[0]
        if raw_label == "UNKNOWN":
            continue
        mapped = LABEL_MAP.get(raw_label, raw_label.upper().replace(" ", "_"))
        for point in ann.get("points") or []:
            start = int(point.get("start", -1))
            end = int(point.get("end", -1))
            if start < 0 or end <= start or end > len(text):
                continue
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            if end <= start:
                continue
            span_len = end - start
            # Split oversized multi-line skill/company blocks into line phrases
            if span_len > 60 and mapped in {"SKILL", "COMPANY", "DESIGNATION"}:
                entities.extend(_split_span_to_lines(text, start, end, mapped))
            elif span_len <= 120:
                entities.append((start, end, mapped))

    entities = _dedupe_overlaps(entities)
    entities = _filter_aligned_entities(text, entities)
    if not entities:
        return None
    return text, {"entities": entities}


def _split_span_to_lines(
    text: str, start: int, end: int, label: str
) -> List[Tuple[int, int, str]]:
    """Break a long annotated block into shorter line/phrase entities."""
    chunk = text[start:end]
    results: List[Tuple[int, int, str]] = []
    offset = 0
    for part in chunk.replace("•", "\n").replace("|", "\n").split("\n"):
        # Also split comma-separated skill lists
        phrases = [p.strip(" -\t•*") for p in part.split(",")]
        cursor = chunk.find(part, offset)
        if cursor < 0:
            cursor = offset
        local = 0
        for phrase in phrases:
            if len(phrase) < 2 or len(phrase) > 60:
                continue
            rel = part.find(phrase, local)
            if rel < 0:
                continue
            abs_start = start + cursor + rel
            abs_end = abs_start + len(phrase)
            if text[abs_start:abs_end] == phrase:
                results.append((abs_start, abs_end, label))
            local = rel + len(phrase)
        offset = cursor + len(part)
    return results


def _filter_aligned_entities(
    text: str, entities: List[Tuple[int, int, str]]
) -> List[Tuple[int, int, str]]:
    """Drop spans that do not align to spaCy token boundaries."""
    try:
        import spacy
        from spacy.training import offsets_to_biluo_tags

        nlp = spacy.blank("en")
        doc = nlp.make_doc(text)
        tags = offsets_to_biluo_tags(doc, entities)
        # If any '-' misalignment, keep only entities that don't cause '-'
        if "-" not in tags:
            return entities
        kept: List[Tuple[int, int, str]] = []
        for ent in entities:
            trial_tags = offsets_to_biluo_tags(doc, [ent])
            if "-" not in trial_tags:
                kept.append(ent)
        return kept
    except Exception:
        return entities


def _dedupe_overlaps(entities: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
    """Keep longer spans when overlaps occur (spaCy requirement)."""
    entities = sorted(entities, key=lambda x: (x[0], -(x[1] - x[0])))
    kept: List[Tuple[int, int, str]] = []
    for start, end, label in entities:
        overlap = False
        for ks, ke, _ in kept:
            if not (end <= ks or start >= ke):
                overlap = True
                break
        if not overlap:
            kept.append((start, end, label))
    return kept


def weak_labels_from_resume_data(
    csv_path: Path, max_rows: int = 500
) -> List[Tuple[str, Dict]]:
    """
    Build weak NER examples by locating structured field values inside resume text.

    Uses resume_data.csv columns when present. Returns spaCy-style examples.
    """
    if not csv_path.exists():
        return []

    import pandas as pd

    df = pd.read_csv(csv_path, nrows=max_rows * 3)
    # Normalize column names (handle BOM)
    df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]

    text_col = None
    for candidate in ("resume_text", "Resume", "resume", "cv_text", "text"):
        if candidate in df.columns:
            text_col = candidate
            break
    if text_col is None:
        # Try to find a long text-like column
        for col in df.columns:
            if df[col].dtype == object:
                sample = str(df[col].dropna().iloc[0]) if df[col].notna().any() else ""
                if len(sample) > 200:
                    text_col = col
                    break
    if text_col is None:
        return []

    field_map = {
        "SKILL": ["skills", "skill", "Skills"],
        "DEGREE": ["degree_names", "degree", "Education", "education"],
        "COMPANY": ["professional_company_names", "company", "companies"],
        "DESIGNATION": ["positions", "position", "job_title", "designation"],
        "COLLEGE": ["educational_institution", "college", "university"],
        "EMAIL": ["email", "Email"],
        "NAME": ["name", "Name", "candidate_name"],
    }

    examples: List[Tuple[str, Dict]] = []
    for _, row in df.iterrows():
        text = str(row.get(text_col) or "")
        if len(text) < 100:
            continue
        entities: List[Tuple[int, int, str]] = []
        for label, cols in field_map.items():
            value = None
            for c in cols:
                if c in df.columns and pd.notna(row.get(c)):
                    value = str(row.get(c))
                    break
            if not value or value.lower() in ("nan", "none", ""):
                continue
            # Take first token/phrase
            phrases = [p.strip() for p in str(value).replace("|", ",").split(",") if p.strip()]
            for phrase in phrases[:3]:
                if len(phrase) < 2:
                    continue
                idx = text.lower().find(phrase.lower())
                if idx >= 0:
                    entities.append((idx, idx + len(phrase), label))
        entities = _dedupe_overlaps(entities)
        cleaned_ents: List[Tuple[int, int, str]] = []
        for s, e, l in entities:
            if e - s > 80:
                continue
            while s < e and text[s].isspace():
                s += 1
            while e > s and text[e - 1].isspace():
                e -= 1
            if e > s and text[s:e] == text[s:e].strip():
                cleaned_ents.append((s, e, l))
        cleaned_ents = _filter_aligned_entities(text[:5000], cleaned_ents)
        if len(cleaned_ents) >= 2:
            examples.append((text[:5000], {"entities": cleaned_ents}))
        if len(examples) >= max_rows:
            break
    return examples


def load_it_ner_json(path: Path) -> List[Dict[str, Any]]:
    """Load ScreenWise IT NER JSON array format."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array in {path}")
    return data


def it_record_to_spacy_example(record: Dict[str, Any]) -> Optional[Tuple[str, Dict]]:
    """Convert IT NER record {text, entities: [[s,e,label],...]} to spaCy example."""
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
        if not text[start:end].strip():
            continue
        entities.append((start, end, label))

    entities = _dedupe_overlaps(entities)
    entities = _filter_aligned_entities(text, entities)
    if not entities:
        return None
    return text, {"entities": entities}


def load_it_ner_splits(
    train_path: Path,
    val_path: Path,
    test_path: Path,
) -> Tuple[
    List[Tuple[str, Dict]],
    List[Tuple[str, Dict]],
    List[Tuple[str, Dict]],
]:
    """Load pre-split IT NER train/val/test without shuffling or leakage."""
    train: List[Tuple[str, Dict]] = []
    val: List[Tuple[str, Dict]] = []
    test: List[Tuple[str, Dict]] = []

    for rec in load_it_ner_json(train_path):
        ex = it_record_to_spacy_example(rec)
        if ex:
            train.append(ex)
    for rec in load_it_ner_json(val_path):
        ex = it_record_to_spacy_example(rec)
        if ex:
            val.append(ex)
    for rec in load_it_ner_json(test_path):
        ex = it_record_to_spacy_example(rec)
        if ex:
            test.append(ex)

    return train, val, test


def build_dataset(
    ner_json_path: Path,
    resume_data_csv: Optional[Path] = None,
    weak_rows: int = 300,
    seed: int = 42,
) -> Tuple[List[Tuple[str, Dict]], List[Tuple[str, Dict]]]:
    records = load_ner_jsonl(ner_json_path)
    examples: List[Tuple[str, Dict]] = []
    for rec in records:
        ex = annotations_to_spacy_example(rec)
        if ex:
            examples.append(ex)

    if resume_data_csv:
        examples.extend(weak_labels_from_resume_data(resume_data_csv, max_rows=weak_rows))

    random.Random(seed).shuffle(examples)
    split = max(1, int(len(examples) * 0.8))
    train = examples[:split]
    test = examples[split:] or examples[-max(1, len(examples) // 5) :]
    return train, test
