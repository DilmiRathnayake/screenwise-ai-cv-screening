"""Rule/section-based resume parsers for fields poorly covered by NER."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from app.schemas.models import (
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
)
from app.utils.text_cleaning import (
    SOFT_SKILLS,
    TECH_HINTS,
    extract_emails,
    extract_phones,
    extract_urls,
)

SECTION_HEADERS = {
    "education": r"education|academic|qualification",
    "experience": r"experience|employment|work history|professional experience",
    "skills": r"skills|technical skills|competencies|technologies",
    "projects": r"projects|personal projects|portfolio projects",
    "certifications": r"certifications?|licenses?|credentials",
    "awards": r"awards?|honou?rs?|achievements",
    "languages": r"languages",
    "publications": r"publications?|research",
    "references": r"references",
    "summary": r"summary|profile|objective|about me",
}


class SectionParser:
    """Heuristic section splitter and field extractors."""

    def parse(self, text: str) -> Dict:
        sections = self._split_sections(text)
        email = (extract_emails(text) or [None])[0]
        phones = extract_phones(text)
        linkedin = (extract_urls(text, "linkedin.com") or [None])[0]
        github = (extract_urls(text, "github.com") or [None])[0]
        portfolio = self._guess_portfolio(text, linkedin, github)

        skills_block = sections.get("skills", "")
        technical, soft = self._parse_skills(skills_block or text)

        return {
            "email": email,
            "phone": phones[0] if phones else None,
            "linkedin": linkedin,
            "github": github,
            "portfolio": portfolio,
            "address": self._guess_address(text),
            "education": self._parse_education(sections.get("education", "")),
            "experience": self._parse_experience(sections.get("experience", "")),
            "technical_skills": technical,
            "soft_skills": soft,
            "languages": self._parse_list_block(sections.get("languages", "")),
            "projects": self._parse_projects(sections.get("projects", "")),
            "certifications": self._parse_list_block(sections.get("certifications", "")),
            "awards": self._parse_list_block(sections.get("awards", "")),
            "publications": self._parse_list_block(sections.get("publications", "")),
            "references": self._parse_list_block(sections.get("references", "")),
            "years_of_experience": self._guess_years(text),
            "sections_found": list(sections.keys()),
        }

    def _split_sections(self, text: str) -> Dict[str, str]:
        lines = (text or "").splitlines()
        indices: List[Tuple[int, str]] = []
        for i, line in enumerate(lines):
            compact = line.strip().lower()
            if not compact or len(compact) > 60:
                continue
            for name, pattern in SECTION_HEADERS.items():
                if re.fullmatch(rf"(?:{pattern})\s*:?", compact):
                    indices.append((i, name))
                    break
        if not indices:
            return {}

        sections: Dict[str, str] = {}
        for idx, (start, name) in enumerate(indices):
            end = indices[idx + 1][0] if idx + 1 < len(indices) else len(lines)
            body = "\n".join(lines[start + 1 : end]).strip()
            sections[name] = body
        return sections

    def _parse_skills(self, block: str) -> Tuple[List[str], List[str]]:
        # Stop at next obvious section heading leaked into the block
        block = re.split(
            r"(?im)\n(?=(?:experience|education|projects|certifications|awards)\b)",
            block,
            maxsplit=1,
        )[0]
        tokens = re.split(r"[,|/•\n;]+", block)
        technical: List[str] = []
        soft: List[str] = []
        for tok in tokens:
            skill = tok.strip(" -\t").strip()
            if len(skill) < 2 or len(skill) > 40:
                continue
            if "xxnewlinexx" in skill.lower() or skill.startswith("+"):
                continue
            # Drop tokens that look like section bleed
            if re.search(
                r"(?i)\b(certifications?|education|experience|projects)\b", skill
            ):
                continue
            low = skill.lower()
            if low in SOFT_SKILLS or any(s in low for s in SOFT_SKILLS):
                soft.append(skill)
            else:
                technical.append(skill)
        technical = list(dict.fromkeys(technical))[:40]
        soft = list(dict.fromkeys(soft))[:20]
        return technical, soft

    def _parse_education(self, block: str) -> List[EducationEntry]:
        if not block:
            return []
        entries: List[EducationEntry] = []
        chunks = re.split(r"\n{2,}|(?=\b(?:B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|Bachelor|Master|Diploma)\b)", block)
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) < 5:
                continue
            year = None
            ym = re.search(r"(19|20)\d{2}", chunk)
            if ym:
                year = ym.group(0)
            degree = None
            dm = re.search(
                r"(Bachelor[^\n,]*|Master[^\n,]*|Ph\.?D\.?[^\n,]*|B\.?Sc?[^\n,]*|M\.?Sc?[^\n,]*|MBA[^\n,]*)",
                chunk,
                re.IGNORECASE,
            )
            if dm:
                degree = dm.group(1).strip()
            university = None
            um = re.search(
                r"(University[^\n,]*|College[^\n,]*|Institute[^\n,]*)",
                chunk,
                re.IGNORECASE,
            )
            if um:
                university = um.group(1).strip()
            if degree or university:
                entries.append(
                    EducationEntry(
                        university=university,
                        degree=degree,
                        graduation_year=year,
                    )
                )
        return entries[:8]

    def _parse_experience(self, block: str) -> List[ExperienceEntry]:
        if not block:
            return []
        entries: List[ExperienceEntry] = []
        chunks = re.split(r"\n(?=[A-Z][^\n]{0,60}\n)", block)
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) < 8:
                continue
            lines = [l.strip() for l in chunk.splitlines() if l.strip()]
            title = lines[0] if lines else None
            company = lines[1] if len(lines) > 1 else None
            duration = None
            dm = re.search(
                r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}"
                r"|\d{4})\s*[-–to]+\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                r"[a-z]*\.?\s+\d{4}|Present|Current|\d{4})",
                chunk,
                re.IGNORECASE,
            )
            if dm:
                duration = dm.group(0)
            entries.append(
                ExperienceEntry(
                    company=company,
                    job_title=title,
                    duration=duration,
                    description=" ".join(lines[2:6]) if len(lines) > 2 else None,
                )
            )
        return entries[:12]

    def _parse_projects(self, block: str) -> List[ProjectEntry]:
        if not block:
            return []
        projects: List[ProjectEntry] = []
        for line in re.split(r"\n+", block):
            line = line.strip(" -•*\t")
            if len(line) < 5:
                continue
            techs = [t for t in TECH_HINTS if t in line.lower()]
            projects.append(
                ProjectEntry(
                    name=line[:80],
                    description=line,
                    technologies=techs,
                )
            )
        return projects[:10]

    def _parse_list_block(self, block: str) -> List[str]:
        if not block:
            return []
        items = re.split(r"[,|\n•;]+", block)
        cleaned = []
        for item in items:
            val = item.strip(" -\t")
            if 2 <= len(val) <= 120:
                cleaned.append(val)
        return list(dict.fromkeys(cleaned))[:20]

    def _guess_portfolio(
        self, text: str, linkedin: Optional[str], github: Optional[str]
    ) -> Optional[str]:
        urls = extract_urls(text)
        for url in urls:
            low = url.lower()
            if linkedin and linkedin in url:
                continue
            if github and github in url:
                continue
            if any(x in low for x in ("portfolio", "behance", "dribbble", "vercel.app", "netlify")):
                return url
        return None

    def _guess_address(self, text: str) -> Optional[str]:
        m = re.search(
            r"(?im)^(?:address|location)\s*[:\-]\s*(.+)$",
            text,
        )
        if m:
            return m.group(1).strip()[:200]
        return None

    def _guess_years(self, text: str) -> Optional[float]:
        m = re.search(
            r"(\d+(?:\.\d+)?)\+?\s*(?:\+)?\s*years?\s+(?:of\s+)?experience",
            text,
            re.IGNORECASE,
        )
        if m:
            return float(m.group(1))
        return None
