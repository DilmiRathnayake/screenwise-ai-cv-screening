"""CV information extraction service (OCR + NER + section parser)."""

from __future__ import annotations

import time
from typing import Optional

from app.repositories.ner_repository import NERRepository
from app.schemas.models import (
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
    ExtractResponse,
)
from app.services.ocr_service import OCRService
from app.services.section_parser import SectionParser
from app.utils.communication_score import score_communication
from app.utils.logging_config import get_logger
from app.utils.text_cleaning import clean_text, extract_emails

logger = get_logger(__name__)


class ExtractionService:
    def __init__(
        self,
        ocr: Optional[OCRService] = None,
        ner: Optional[NERRepository] = None,
        parser: Optional[SectionParser] = None,
    ) -> None:
        self.ocr = ocr or OCRService()
        self.ner = ner or NERRepository()
        self.parser = parser or SectionParser()

    @property
    def ner_loaded(self) -> bool:
        return self.ner.is_loaded

    def extract_from_bytes(self, filename: str, content: bytes) -> ExtractResponse:
        started = time.perf_counter()
        raw_text, method = self.ocr.extract_text(filename, content)
        profile = self.extract_from_text(raw_text, source_method=method)
        elapsed = (time.perf_counter() - started) * 1000
        return ExtractResponse(
            success=True,
            filename=filename,
            profile=profile,
            processing_ms=round(elapsed, 2),
        )

    def extract_from_text(self, text: str, source_method: str = "text") -> CandidateProfile:
        # Contact fields from raw text before URL/email cleaning
        raw_emails = extract_emails(text)
        from app.utils.text_cleaning import extract_phones, extract_urls

        raw_phones = extract_phones(text)
        linkedin = (extract_urls(text, "linkedin.com") or [None])[0]
        github = (extract_urls(text, "github.com") or [None])[0]

        cleaned = clean_text(text, keep_emails=True, lowercase=False)
        parsed = self.parser.parse(cleaned)
        entities = self.ner.predict(cleaned)
        comm = score_communication(cleaned)

        name = (entities.get("NAME") or [None])[0] or self._guess_name(cleaned)
        email = (entities.get("EMAIL") or [None])[0] or (raw_emails[0] if raw_emails else None) or parsed.get("email")
        location = (entities.get("LOCATION") or [None])[0] or parsed.get("address")

        # Merge skills
        ner_skills = entities.get("SKILL") or []
        technical = list(dict.fromkeys((parsed.get("technical_skills") or []) + ner_skills))
        soft = parsed.get("soft_skills") or []

        education = parsed.get("education") or []
        if not education:
            education = self._education_from_ner(entities)

        experience = parsed.get("experience") or []
        if not experience:
            experience = self._experience_from_ner(entities)

        yoe = parsed.get("years_of_experience")
        if yoe is None and entities.get("YOE"):
            try:
                import re

                m = re.search(r"(\d+(?:\.\d+)?)", entities["YOE"][0])
                yoe = float(m.group(1)) if m else None
            except Exception:
                yoe = None
        if yoe is None:
            yoe = self.parser._guess_years(cleaned)

        ner_certs = entities.get("CERTIFICATION") or []
        certifications = list(
            dict.fromkeys((parsed.get("certifications") or []) + ner_certs)
        )

        return CandidateProfile(
            name=name,
            email=email,
            phone=(raw_phones[0] if raw_phones else None) or parsed.get("phone"),
            address=location,
            linkedin=linkedin or parsed.get("linkedin"),
            github=github or parsed.get("github"),
            portfolio=parsed.get("portfolio"),
            education=education,
            experience=experience,
            technical_skills=technical,
            soft_skills=soft,
            languages=parsed.get("languages") or [],
            projects=parsed.get("projects") or [],
            publications=parsed.get("publications") or [],
            certifications=certifications,
            awards=parsed.get("awards") or [],
            references=parsed.get("references") or [],
            years_of_experience=yoe,
            communication_score=comm["communication_score"],
            raw_text=cleaned[:50000],
            extraction_meta={
                "source_method": source_method,
                "ner_loaded": self.ner.is_loaded,
                "sections_found": parsed.get("sections_found") or [],
                "communication_breakdown": {
                    k: v for k, v in comm.items() if k != "communication_score"
                },
                "ner_entity_counts": {k: len(v) for k, v in entities.items() if v},
            },
        )

    def _guess_name(self, text: str) -> Optional[str]:
        for line in text.splitlines()[:8]:
            line = line.strip()
            if not line or "@" in line or len(line) > 60:
                continue
            if any(ch.isdigit() for ch in line):
                continue
            if line.lower() in {
                "summary",
                "skills",
                "experience",
                "education",
                "projects",
                "objective",
                "profile",
            }:
                continue
            words = line.split()
            if 2 <= len(words) <= 5 and all(
                w.replace("-", "").isalpha() and w[0].isupper() for w in words
            ):
                return line
        return None

    def _education_from_ner(self, entities: dict) -> list[EducationEntry]:
        degrees = entities.get("DEGREE") or []
        colleges = entities.get("COLLEGE") or []
        years = entities.get("GRAD_YEAR") or []
        n = max(len(degrees), len(colleges), 1 if (degrees or colleges) else 0)
        entries = []
        for i in range(n):
            entries.append(
                EducationEntry(
                    degree=degrees[i] if i < len(degrees) else None,
                    university=colleges[i] if i < len(colleges) else None,
                    graduation_year=years[i] if i < len(years) else None,
                )
            )
        return entries

    def _experience_from_ner(self, entities: dict) -> list[ExperienceEntry]:
        companies = entities.get("COMPANY") or []
        titles = entities.get("DESIGNATION") or []
        n = max(len(companies), len(titles))
        entries = []
        for i in range(n):
            entries.append(
                ExperienceEntry(
                    company=companies[i] if i < len(companies) else None,
                    job_title=titles[i] if i < len(titles) else None,
                )
            )
        return entries
