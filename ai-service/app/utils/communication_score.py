"""Communication quality scoring (rule-based proxy — no labeled dataset)."""

import re
from typing import Dict

try:
    import textstat
except ImportError:  # pragma: no cover
    textstat = None


def score_communication(text: str) -> Dict[str, float]:
    """
    Return communication_score in [0, 1] plus component breakdown.

    Uses readability, structure, and lexical diversity as proxies for CV
    writing quality (proposal criterion without labeled training data).
    """
    if not text or len(text.strip()) < 40:
        return {
            "communication_score": 0.3,
            "readability": 0.3,
            "structure": 0.3,
            "lexical_diversity": 0.3,
        }

    words = re.findall(r"[A-Za-z]+", text.lower())
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    unique = set(words)

    # Readability: map Flesch Reading Ease (~0-100) into 0-1
    if textstat is not None:
        try:
            fre = float(textstat.flesch_reading_ease(text))
            readability = max(0.0, min(1.0, fre / 100.0))
        except Exception:
            readability = 0.5
    else:
        avg_len = (len(words) / max(len(sentences), 1))
        readability = max(0.0, min(1.0, 1.0 - abs(avg_len - 18) / 30))

    # Structure: presence of section-like headings and bullets
    heading_hits = len(
        re.findall(
            r"(?im)^(education|experience|skills|projects|certifications|"
            r"summary|objective|achievements|awards)\b",
            text,
        )
    )
    bullet_hits = len(re.findall(r"(?m)^\s*[-*•]\s+", text))
    structure = min(1.0, (heading_hits * 0.15) + (bullet_hits * 0.02) + 0.2)

    # Lexical diversity
    diversity = (len(unique) / max(len(words), 1)) if words else 0.0
    lexical = min(1.0, diversity * 2.5)

    # Spelling proxy: ratio of short/odd tokens
    odd = sum(1 for w in words if len(w) > 20 or re.search(r"(.)\1{3,}", w))
    spelling = max(0.0, 1.0 - (odd / max(len(words), 1)) * 10)

    score = (
        0.35 * readability
        + 0.30 * structure
        + 0.20 * lexical
        + 0.15 * spelling
    )
    score = round(max(0.0, min(1.0, score)), 4)

    return {
        "communication_score": score,
        "readability": round(readability, 4),
        "structure": round(structure, 4),
        "lexical_diversity": round(lexical, 4),
        "spelling_proxy": round(spelling, 4),
    }
