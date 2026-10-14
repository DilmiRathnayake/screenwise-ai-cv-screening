"""Unit tests for OCR, section parser, ranking weights, and API health."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.configs.ranking_weights import get_industry_weights, normalize_weights
from app.main import app
from app.schemas.models import (
    CandidateProfile,
    EducationEntry,
    JobRequirements,
    ProjectEntry,
    RankCandidateInput,
    RankRequest,
)
from app.services.ocr_service import OCRService
from app.services.ranking_service import RankingService
from app.services.section_parser import SectionParser
from app.utils.communication_score import score_communication


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "ner_model_loaded" in data


def test_industry_weights_sum_to_one():
    for industry in ("it", "default", "tech"):
        weights = get_industry_weights(industry)
        assert abs(sum(weights.values()) - 1.0) < 1e-6
    it_w = get_industry_weights("it")
    assert it_w["technical_skills"] == pytest.approx(0.35, abs=1e-6)


def test_normalize_weights():
    w = normalize_weights({"technical_skills": 2, "experience": 2})
    assert abs(sum(w.values()) - 1.0) < 1e-6
    assert set(w.keys()) == {
        "technical_skills",
        "experience",
        "projects",
        "education",
        "communication",
        "certifications",
    }


def test_section_parser_extracts_contact_and_skills():
    text = """
Jane Doe
jane.doe@email.com
+1 555-123-4567
https://linkedin.com/in/janedoe
https://github.com/janedoe

Skills
Python, React, Leadership, Communication

Experience
Software Engineer
Acme Corp
Jan 2020 - Present
Built APIs with FastAPI

Education
B.Sc. Computer Science
State University
2019
"""
    parsed = SectionParser().parse(text)
    assert parsed["email"] == "jane.doe@email.com"
    assert parsed["linkedin"]
    assert parsed["github"]
    assert any("Python" in s or "python" in s.lower() for s in parsed["technical_skills"])
    assert parsed["years_of_experience"] is None or isinstance(parsed["years_of_experience"], float)


def test_communication_score_range():
    score = score_communication(
        "Summary\nExperienced engineer.\n\nSkills\n- Python\n- Leadership\n\n"
        "Education\nBachelor of Science."
    )
    assert 0.0 <= score["communication_score"] <= 1.0


def test_ocr_docx():
    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph("John Smith")
    doc.add_paragraph("john.smith@example.com")
    doc.add_paragraph("Skills: Python, SQL, Docker")
    doc.save(buf)
    text, method = OCRService().extract_text("resume.docx", buf.getvalue())
    assert method == "python-docx"
    assert "John Smith" in text
    assert "Python" in text


def test_ranking_orders_better_candidate_higher():
    class LexicalEmb:
        is_loaded = False

        def section_similarity(self, job_text, sections):
            raise RuntimeError("force lexical")

    service = RankingService(embeddings=LexicalEmb())  # type: ignore
    job = JobRequirements(
        title="React Developer",
        description="Need React Developer with three years experience in TypeScript",
        required_skills=["React", "TypeScript", "JavaScript"],
        minimum_experience=3,
        education_level="Bachelor",
        industry="it",
    )
    strong = CandidateProfile(
        name="Strong Cand",
        technical_skills=["React", "TypeScript", "JavaScript", "Node"],
        years_of_experience=4,
        education=[EducationEntry(degree="Bachelor of Science")],
        projects=[ProjectEntry(name="App", technologies=["React", "TypeScript"])],
        communication_score=0.6,
        raw_text="React TypeScript JavaScript developer with 4 years experience",
    )
    weak = CandidateProfile(
        name="Weak Cand",
        technical_skills=["Excel", "Word"],
        years_of_experience=0,
        education=[EducationEntry(degree="High School")],
        projects=[],
        communication_score=0.3,
        raw_text="Office assistant with Excel",
    )
    resp = service.rank(
        RankRequest(
            job=job,
            candidates=[
                RankCandidateInput(candidate_id="1", profile=strong),
                RankCandidateInput(candidate_id="2", profile=weak),
            ],
        )
    )
    assert resp.top_candidates[0].candidate_id == "1"
    assert resp.top_candidates[0].matching_percentage > resp.top_candidates[1].matching_percentage
    assert resp.top_candidates[0].ranking_explanation


def test_rank_api(client):
    payload = {
        "job": {
            "title": "Data Analyst",
            "description": "SQL and Python analyst role",
            "required_skills": ["SQL", "Python"],
            "minimum_experience": 2,
            "industry": "it",
        },
        "candidates": [
            {
                "candidate_id": "c1",
                "profile": {
                    "name": "Alex",
                    "technical_skills": ["SQL", "Python", "Tableau"],
                    "years_of_experience": 3,
                    "communication_score": 0.7,
                    "raw_text": "Data analyst SQL Python Tableau",
                },
            }
        ],
    }
    resp = client.post("/api/v1/rank", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["total_candidates"] == 1
    assert data["top_candidates"][0]["matching_percentage"] > 0


def test_weights_endpoint(client):
    resp = client.get("/api/v1/ranking/weights/it")
    assert resp.status_code == 200
    data = resp.json()
    assert data["weights"]["technical_skills"] >= data["weights"]["certifications"]
    assert abs(sum(data["weights"].values()) - 1.0) < 1e-6
