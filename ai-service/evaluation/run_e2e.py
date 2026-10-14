"""End-to-end: extract from sample DOCX/text → rank against a sample job."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.models import JobRequirements, RankCandidateInput, RankRequest
from app.services.extraction_service import ExtractionService
from app.services.ranking_service import RankingService


def _sample_docx_bytes() -> bytes:
    buf = io.BytesIO()
    doc = Document()
    doc.add_heading("Priya Fernando", level=1)
    doc.add_paragraph("priya.fernando@email.com | +94 77 123 4567")
    doc.add_paragraph("https://linkedin.com/in/priyafernando | https://github.com/priyaf")
    doc.add_heading("Summary", level=2)
    doc.add_paragraph(
        "React developer with three years experience building HR dashboards and APIs."
    )
    doc.add_heading("Skills", level=2)
    doc.add_paragraph("React, TypeScript, JavaScript, Node.js, FastAPI, MySQL, Git")
    doc.add_heading("Experience", level=2)
    doc.add_paragraph("Frontend Engineer")
    doc.add_paragraph("TechNova Pvt Ltd")
    doc.add_paragraph("Jan 2022 - Present")
    doc.add_paragraph("Built recruitment analytics UI with React and Chart.js.")
    doc.add_heading("Education", level=2)
    doc.add_paragraph("B.Sc. Computer Science — University of Colombo — 2021")
    doc.add_heading("Projects", level=2)
    doc.add_paragraph("CV Screening Dashboard — React, TypeScript, Chart.js")
    doc.add_heading("Certifications", level=2)
    doc.add_paragraph("AWS Cloud Practitioner")
    doc.save(buf)
    return buf.getvalue()


def main() -> None:
    extraction = ExtractionService()
    ranking = RankingService()

    extract_resp = extraction.extract_from_bytes("sample_cv.docx", _sample_docx_bytes())
    profile = extract_resp.profile

    job = JobRequirements(
        title="React Developer",
        description="React Developer with three years experience in TypeScript and Node.js",
        required_skills=["React", "TypeScript", "JavaScript", "Node.js"],
        minimum_experience=3,
        education_level="Bachelor",
        industry="it",
        required_certifications=["AWS"],
    )

    # Weaker rival candidate
    from app.schemas.models import CandidateProfile, EducationEntry

    weak = CandidateProfile(
        name="Sam Office",
        technical_skills=["Excel", "Word"],
        years_of_experience=1,
        education=[EducationEntry(degree="Diploma")],
        communication_score=0.4,
        raw_text="Office assistant Excel Word",
    )

    rank_resp = ranking.rank(
        RankRequest(
            job=job,
            candidates=[
                RankCandidateInput(candidate_id="extracted", profile=profile),
                RankCandidateInput(candidate_id="weak", profile=weak),
            ],
        )
    )

    report = {
        "extraction": {
            "filename": extract_resp.filename,
            "processing_ms": extract_resp.processing_ms,
            "name": profile.name,
            "email": profile.email,
            "skills": profile.technical_skills[:10],
            "communication_score": profile.communication_score,
            "ner_loaded": profile.extraction_meta.get("ner_loaded"),
            "source_method": profile.extraction_meta.get("source_method"),
        },
        "ranking": {
            "job_title": rank_resp.job_title,
            "industry": rank_resp.industry,
            "weights_used": rank_resp.weights_used,
            "top_candidates": [
                {
                    "candidate_id": c.candidate_id,
                    "name": c.name,
                    "matching_percentage": c.matching_percentage,
                    "ranking_position": c.ranking_position,
                    "explanation": c.ranking_explanation,
                }
                for c in rank_resp.top_candidates
            ],
        },
    }

    out = ROOT / "models" / "e2e_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
