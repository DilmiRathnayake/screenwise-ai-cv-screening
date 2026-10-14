"""IT skill normalization and synonym mapping for ranking."""

from __future__ import annotations

from app.utils.text_cleaning import normalize_for_matching

# Canonical form -> aliases (lowercase)
IT_SKILL_SYNONYMS: dict[str, list[str]] = {
    "python": ["py", "python3"],
    "javascript": ["js", "ecmascript"],
    "typescript": ["ts"],
    "react": ["reactjs", "react.js"],
    "node": ["nodejs", "node.js"],
    "vue": ["vuejs", "vue.js"],
    "angular": ["angularjs"],
    "kubernetes": ["k8s"],
    "docker": ["containerization"],
    "postgresql": ["postgres", "psql"],
    "mongodb": ["mongo"],
    "amazon web services": ["aws"],
    "google cloud": ["gcp", "google cloud platform"],
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "pytorch": ["torch"],
    "tensorflow": ["tf"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "c++": ["cpp"],
    "c#": ["csharp", "c sharp"],
    "git": ["github", "gitlab"],
    "ci/cd": ["cicd", "continuous integration"],
    "rest": ["restful", "rest api"],
    "fastapi": ["fast api"],
    "spring boot": ["springboot"],
    "express": ["expressjs", "express.js"],
    "next.js": ["nextjs"],
    "flask": ["flask framework"],
    "django": ["django rest"],
    "redis": ["redis cache"],
    "mysql": ["mariadb"],
    "html": ["html5"],
    "css": ["css3"],
}


def normalize_it_skill(skill: str) -> str:
    """Normalize an IT skill to a canonical token for matching."""
    s = normalize_for_matching(skill)
    s = s.replace(".js", "").replace(".ts", "").replace(".py", "")
    s = s.replace(" ", "")
    if not s:
        return ""

    for canonical, aliases in IT_SKILL_SYNONYMS.items():
        canon = canonical.replace(" ", "").replace(".", "")
        if s == canon or s in [a.replace(" ", "") for a in aliases]:
            return canon
        for alias in aliases:
            al = alias.replace(" ", "").replace(".", "")
            if s == al or (len(s) > 2 and (s in al or al in s)):
                return canon
    return s
