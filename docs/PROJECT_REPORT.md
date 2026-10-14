# ScreenWise — Final Year Project Report Guide

**Project title:** AI-Based Intelligent CV Screening and Candidate Ranking System for IT Recruitment  
**Product name:** ScreenWise  
**Report date:** September 2026  

This document is a structured guide for writing your dissertation / viva report. All metrics below are from **held-out test sets** stored in the repository (not hardcoded UI values).

---

## 1. Executive summary

ScreenWise is a three-tier web application that automates IT recruitment screening:

1. **Model 1** extracts structured information from CV files (PDF/DOCX/images) using OCR + spaCy NER.
2. **Model 2** ranks candidates against job requirements using embeddings, weighted criteria, and a LightGBM LambdaMART ranker trained on an IT-specific dataset.
3. A **React** HR workspace lets recruiters upload CVs, run ranking, view explainable scores, search semantically, and schedule interviews.

**Reportable overall accuracy (test sets):**

| Component | Metric | Value |
|-----------|--------|-------|
| Model 1 — extraction | Entity-level accuracy | **97.6%** |
| Model 2 — ranking | Top-1 best-candidate accuracy | **100%** |
| Model 2 — ranking | NDCG@5 (list quality) | **100%** |
| Combined (simple average) | — | **≈ 98.8%** |

*Model 2 metrics are on the synthetic IT ranking test set (`model2_it/`). Model 1 metrics are on 150 held-out IT CVs.*

---

## 2. Problem statement

Traditional CV screening is slow, inconsistent, and biased toward keyword matching. ScreenWise addresses:

- Manual extraction of skills, education, and experience from heterogeneous CV formats.
- Subjective, non-repeatable shortlisting when many candidates apply per role.
- Lack of explainability when rejecting or advancing candidates.

**Scope (this research):** Information Technology recruitment only (Model 2 dataset and evaluation).

---

## 3. Objectives

| # | Objective | Status |
|---|-----------|--------|
| 1 | Build a CV information extraction pipeline (OCR + NER) | ✅ Model 1 |
| 2 | Build an explainable candidate ranking system for IT jobs | ✅ Model 2 |
| 3 | Create a controlled IT ranking dataset with leakage-safe splits | ✅ `model2_it/` |
| 4 | Train and evaluate ML ranker (LightGBM LambdaMART) vs baseline | ✅ |
| 5 | Deliver a full-stack demo (upload → extract → rank → UI) | ✅ |
| 6 | Wire UI metrics to real evaluation JSON | ✅ Landing page + API |

---

## 4. System architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (React + Vite)          http://localhost:5173          │
│  Landing · Admin · HR workspace · Job detail · AI ranking       │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST /api/*
┌────────────────────────────▼────────────────────────────────────┐
│  Backend (Node.js + Express)       http://localhost:5000        │
│  JWT auth · MySQL · file uploads · AI proxy                     │
└────────────┬───────────────────────────────┬────────────────────┘
             │                               │
┌────────────▼────────────┐    ┌─────────────▼────────────────────┐
│  MySQL 8 (cv_screening) │    │  AI Service (FastAPI) :8000       │
│  jobs, candidates,      │    │  Model 1: spaCy NER + OCR         │
│  rankings, interviews   │    │  Model 2: embeddings + LGBM rank  │
└─────────────────────────┘    └───────────────────────────────────┘
```

**Trust boundary:** The browser never calls the AI service directly. All ML goes through the backend.

---

## 5. Technology stack

| Layer | Technologies |
|-------|----------------|
| Frontend | React 19, Vite, Tailwind CSS, TanStack Query, Recharts, FullCalendar |
| Backend | Node.js 18+, Express, MySQL2, JWT, Multer, Winston |
| AI service | Python 3.11+, FastAPI, spaCy, PyMuPDF, Sentence-Transformers, LightGBM |
| Database | MySQL 8.0 |
| Deployment | Docker Compose (optional) |

---

## 6. Model 1 — CV information extraction

### 6.1 Purpose

Convert uploaded CV files into structured JSON: name, email, skills, degree, certifications, experience, projects.

### 6.2 Method

| Step | Technique |
|------|-----------|
| Text acquisition | PyMuPDF (PDF), python-docx (DOCX), Tesseract (images) |
| Entity recognition | spaCy NER trained on IT dataset (5 labels) |
| Structure | Rule-based section parser for fields not in NER |
| Optional fallback | Gemini OCR when text quality is poor |

### 6.3 Dataset

| Split | Records | File |
|-------|---------|------|
| Train | 700 | `it_ner_train.json` |
| Validation | 150 | `it_ner_val.json` |
| Test | 150 | `it_ner_test.json` |

**Entity labels:** NAME, EMAIL, SKILL, DEGREE, CERTIFICATION

### 6.4 Results (held-out test, n=150 CVs)

| Metric | Legacy baseline | IT model (after) |
|--------|-----------------|------------------|
| Accuracy | 22.5% | **97.6%** |
| Precision | 47.5% | **97.6%** |
| Recall | 29.9% | **100%** |
| F1 | 36.7% | **98.8%** |

**Source:** `ai-service/models/extraction/metrics.json`

### 6.5 Artifacts

- Trained model: `ai-service/models/extraction/ner_model/`
- Training script: `ai-service/training/train_ner.py`

---

## 7. Model 2 — IT candidate ranking

### 7.1 Purpose

Given a job description and a pool of candidates, produce an **ordered ranking** with explainable criterion scores.

### 7.2 Two implementations

| Track | Location | Role |
|-------|----------|------|
| **Production ranker** | `ai-service/` (runtime `/api/v1/rank`) | Live app ranking with weighted criteria + LightGBM blend |
| **Research pipeline** | `model2_it/` | Dataset generation, feature engineering, LambdaMART training, evaluation |

Your report should emphasize **`model2_it/`** for methodology and reproducible metrics.

### 7.3 Dataset (`model2_it/datasets/model2_it/`)

| Property | Value |
|----------|-------|
| Total job–candidate pairs | 10,000 |
| Unique jobs | 666 |
| Split method | 70/15/15 by **job_id** (group-aware, no leakage) |
| Train / val / test | 7,184 / 1,400 / 1,416 pairs |
| Test jobs | 101 |

**Key columns:** job requirements, candidate skills/experience/education/text, relevance_score (0–100), relevance_label (0–4).

**Scripts:**

```bash
cd model2_it
python generate_model2_it_dataset.py --samples 10000 --seed 42
python validate_model2_dataset.py --outdir datasets/model2_it
```

### 7.4 Feature engineering

`prepare_model2_features.py` builds features from **raw fields** (not pre-computed match columns):

- Required/preferred skill overlap, missing skills
- Experience and education match (computed from raw)
- Project and certification relevance
- Skill-graph semantic overlap
- Feature interactions (e.g. skill × experience)
- Sentence-Transformer embeddings (`all-MiniLM-L6-v2`, disk-cached)

### 7.5 Training

`train_model2.py`:

- Algorithm: **LightGBM LambdaMART** grouped by `job_id`
- Labels: fine-grained `relevance_score` (0–100)
- Hyperparameter grid search on **validation only** (never test)
- Baseline: required-skill overlap only
- Final blend: ML + rule-based composite (weight tuned on validation)

### 7.6 Results (held-out test, 101 jobs, 1,416 pairs)

**Source:** `model2_it/evaluation/model2_metrics.json`

| Metric | ML + blend (reported) | ML only | Skill baseline |
|--------|----------------------|---------|----------------|
| **Top-1 accuracy** | **100%** | 96.0% | 44.6% |
| NDCG@5 | 100% | 99.97% | 97.6% |
| NDCG@10 | 100% | 99.99% | 98.3% |
| Precision@5 | 86.5% | 86.5% | 83.8% |
| Recall@5 | 80.2% | 80.2% | 77.6% |
| MRR | 100% | 100% | 100% |
| Spearman | 0.914 | 0.954 | 0.903 |

### 7.7 Limitations (include in report)

- Labels are from a **documented synthetic rubric**, not real hiring decisions.
- High top-1/NDCG means the model recovers that rubric on held-out jobs — not guaranteed real-world hiring accuracy.
- Production runtime ranker (`ai-service`) uses a separate IT dataset; integrate `model2_it` model for identical live behaviour.

---

## 8. Application modules

### 8.1 User roles

| Role | Login | Capabilities |
|------|-------|--------------|
| HR Manager | `hr@cvscreening.local` | Jobs, CV upload, ranking, search, interviews |
| Admin | `admin@cvscreening.local` | Dashboard, health, analytics |
| Candidate | Demo only | Local mock portal (no backend auth) |

**Password (seed):** `Password123!`

### 8.2 Main workflows

**A. CV screening**

1. HR creates a job (title, description, industry = IT).
2. Upload CV(s) → backend → AI extract → candidate stored in MySQL.
3. Open job → **Run AI ranking** → scores + criterion breakdown persisted.

**B. Semantic search**

- Natural-language query → embedding search over indexed candidates.

**C. Interviews**

- Schedule / reschedule / cancel from HR workspace (optional n8n/SendGrid hooks).

### 8.3 UI surfaces

| Page | Path | Description |
|------|------|-------------|
| Landing | `/` | Marketing + **live Model 2 accuracy** from API |
| HR dashboard | `/hr/dashboard` | Pipeline KPIs |
| Jobs | `/hr/jobs` | Job list, create, kanban |
| Job detail | `/hr/jobs/:id` | Candidates, **AI ranking tab**, charts |
| Admin | `/admin` | System health, service status |

---

## 9. API reference (summary)

### Backend — `http://localhost:5000`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | DB + AI status |
| `/api/auth/login` | POST | JWT login |
| `/api/jobs` | GET/POST | Jobs CRUD |
| `/api/jobs/:id/cvs` | POST | Upload CV |
| `/api/jobs/:id/rank` | POST | Run ranking |
| `/api/jobs/:id/rankings` | GET | Get stored rankings |
| `/api/ranking/model2/metrics` | GET | **Real Model 2 test metrics** |

### AI service — `http://localhost:8000/api/v1`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | NER + embedding status |
| `/extract` | POST | CV extraction |
| `/rank` | POST | Candidate ranking |
| `/ranking/model2/metrics` | GET | Metrics JSON |

Interactive docs: http://localhost:8000/docs

---

## 10. How to run the system

### Option A — Local development (current setup)

**Terminal 1 — AI service**

```bash
cd ai-service
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Backend**

```bash
cd backend
npm run db:init    # first time only
node src/server.js
```

**Terminal 3 — Frontend**

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

| Service | URL |
|---------|-----|
| **Application UI** | http://127.0.0.1:5173 |
| Backend API | http://127.0.0.1:5000 |
| AI service | http://127.0.0.1:8000 |
| AI Swagger | http://127.0.0.1:8000/docs |

### Option B — Docker Compose

Requires Docker Desktop:

```bash
copy .env.example .env
docker compose up --build
```

UI: http://localhost:8080

### Option C — Retrain Model 2

```bash
cd model2_it
python prepare_model2_features.py
python train_model2.py
python evaluate_model2.py
```

---

## 11. Suggested report chapter outline

1. **Introduction** — problem, scope (IT only), objectives  
2. **Literature review** — ATS, NER, learning-to-rank, explainable AI  
3. **Requirements** — functional / non-functional  
4. **System design** — architecture diagram (Section 4 above)  
5. **Model 1** — dataset, spaCy NER, metrics table (Section 6)  
6. **Model 2** — dataset methodology, features, LambdaMART, evaluation (Section 7)  
7. **Implementation** — stack, key modules, screenshots of HR ranking UI  
8. **Testing** — unit tests (`pytest`), manual E2E workflow  
9. **Results & discussion** — accuracy tables, limitations  
10. **Conclusion & future work** — real resume data, production integration, user study  

---

## 12. Screenshots to capture for the report

1. Landing page showing **Model 2 accuracy 100%** (live from API).  
2. HR login → dashboard.  
3. Job creation form (IT industry).  
4. CV upload success.  
5. Job detail → **AI Ranking** tab with bar chart and criterion breakdown.  
6. Admin → System health (AI + DB green).  
7. AI Swagger `/docs` health + extract endpoint.  
8. Terminal output of `evaluate_model2.py` metrics.  

---

## 13. File reference map

| Topic | Path |
|-------|------|
| Master docs | `docs/DOCUMENTATION.md` |
| Model 1 training | `ai-service/training/train_ner.py` |
| Model 1 metrics | `ai-service/models/extraction/metrics.json` |
| Model 2 dataset README | `model2_it/README_MODEL2_IT_DATASET.md` |
| Model 2 features | `model2_it/prepare_model2_features.py` |
| Model 2 training | `model2_it/train_model2.py` |
| Model 2 evaluation | `model2_it/evaluation/model2_metrics.json` |
| Model 2 report | `model2_it/evaluation/model2_evaluation_report.md` |
| Audit trail | `AUDIT_HISTORY.md` |
| Database schema | `backend/sql/schema.sql` |

---

## 14. Viva demo script (5–10 minutes)

1. Open http://127.0.0.1:5173 — point out live Model 2 accuracy on landing page.  
2. Login as `hr@cvscreening.local`.  
3. Open an existing job or create “Python Developer” (IT).  
4. Upload a sample CV (PDF/DOCX).  
5. Click **Run AI ranking** — show ordered list + scores.  
6. Open http://127.0.0.1:5000/api/health — show AI + DB healthy.  
7. Open http://127.0.0.1:5000/api/ranking/model2/metrics — show JSON test metrics.  
8. Briefly explain train/val/test split by job_id and that test was never used in training.  

---

*Generated for ScreenWise FYP report preparation — September 2026.*
