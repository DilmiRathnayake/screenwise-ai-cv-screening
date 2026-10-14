"""Text cleaning utilities (aligned with research notebook preprocessing)."""

import re
from typing import List

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}"
)
_HASHTAG_RE = re.compile(r"#\w+")
_MENTION_RE = re.compile(r"@\w+")
_NON_ASCII_RE = re.compile(r"[^\x00-\x7F]+")
_MULTI_SPACE_RE = re.compile(r"\s+")


def clean_text(text: str, keep_emails: bool = True, lowercase: bool = False) -> str:
    if not text:
        return ""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    # Protect newlines while collapsing horizontal whitespace
    cleaned = cleaned.replace("\n", " XXNEWLINEXX ")
    cleaned = _URL_RE.sub(" ", cleaned)
    if not keep_emails:
        cleaned = _EMAIL_RE.sub(" ", cleaned)
        cleaned = _MENTION_RE.sub(" ", cleaned)
    cleaned = _HASHTAG_RE.sub(" ", cleaned)
    cleaned = _NON_ASCII_RE.sub(" ", cleaned)
    cleaned = re.sub(r"[^\w\s@.+/\-:(),|]", " ", cleaned)
    cleaned = re.sub(r"[^\S\n]+", " ", cleaned)  # collapse spaces/tabs only
    cleaned = _MULTI_SPACE_RE.sub(" ", cleaned).strip()
    cleaned = cleaned.replace(" XXNEWLINEXX ", "\n").replace("XXNEWLINEXX", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if lowercase:
        cleaned = cleaned.lower()
    return cleaned


def normalize_for_matching(text: str) -> str:
    return clean_text(text, keep_emails=False, lowercase=True)


def extract_emails(text: str) -> List[str]:
    return list(dict.fromkeys(_EMAIL_RE.findall(text or "")))


def extract_phones(text: str) -> List[str]:
    candidates = _PHONE_RE.findall(text or "")
    phones: List[str] = []
    for p in candidates:
        digits = re.sub(r"\D", "", p)
        if 9 <= len(digits) <= 15:
            phones.append(p.strip())
    return list(dict.fromkeys(phones))


def extract_urls(text: str, domain_hint: str | None = None) -> List[str]:
    urls = _URL_RE.findall(text or "")
    if domain_hint:
        urls = [u for u in urls if domain_hint.lower() in u.lower()]
    return list(dict.fromkeys(urls))


SOFT_SKILLS = {
    "communication",
    "leadership",
    "teamwork",
    "problem solving",
    "problem-solving",
    "critical thinking",
    "time management",
    "adaptability",
    "creativity",
    "collaboration",
    "interpersonal",
    "negotiation",
    "presentation",
    "customer service",
    "conflict resolution",
}


TECH_HINTS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "sql",
    "aws",
    "docker",
    "kubernetes",
    "machine learning",
    "deep learning",
    "nlp",
    "tensorflow",
    "pytorch",
    "excel",
    "power bi",
    "tableau",
    "html",
    "css",
    "c++",
    "c#",
    ".net",
    "spring",
    "django",
    "fastapi",
    "mongodb",
    "postgresql",
    "mysql",
    "git",
    "linux",
    "azure",
    "gcp",
}
