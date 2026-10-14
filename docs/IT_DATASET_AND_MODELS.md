# ScreenWise — IT Dataset Integration & Model Accuracy Report

**Project:** ScreenWise — AI-Based Intelligent CV Screening and Candidate Ranking System for IT Recruitment  
**Student:** R.M.D.T. Rathnayake | F20021212011  
**Supervisor:** Ms. Nethmi Thileka Mohotti  
**Report date:** September 2026  
**Scope:** IT recruitment only

---

## 1. System Overview

ScreenWise is a three-tier application:

| Layer | Technology | Role |
|-------|------------|------|
| Frontend | React + Vite | HR workspace, CV upload, ranking UI |
| Backend | Node.js + Express + MySQL | Auth, jobs, candidates, API proxy |
| AI Service | FastAPI + spaCy + Sentence-Transformers | CV extraction (Model 01) and ranking (Model 02) |

### End-to-end flow

```
CV Upload → OCR/Text extraction → Text cleaning → Model 01 (NER + rules) → Candidate JSON
                                                                                    ↓
Job Description + Candidate profiles → Model 02 (weighted scoring + embeddings) → Ranked results
```

---

## 2. Custom IT Datasets

Two datasets were prepared for this research project. Original files are **never modified**; cleaned copies live under `ai-service/datasets/processed/`.

### 2.1 Model 01 — NER Dataset

**Location:** `D:\cv screening\ScreenWise_IT_Datasets_ner`

| File | Records | Purpose |
|------|---------|---------|
| `it_ner_full.json` | 1,000 | All annotated CV texts |
| `it_ner_train.json` | 700 | Training (70%) |
| `it_ner_val.json` | 150 | Validation (15%) |
| `it_ner_test.json` | 150 | **Held-out test (15%)** |
| `it_cv_texts.csv` | 1,000 | Same texts in CSV format |

**Format:** JSON array — each record has `text` and `entities` as `[start, end, "LABEL"]` tuples.

**Entity labels (5):** `NAME`, `EMAIL`, `SKILL`, `DEGREE`, `CERTIFICATION`

**Quality checks:**
- 0 duplicate texts across splits
- 0 train/val/test text overlap
- Mean CV length: ~703 characters

**Fields NOT in NER labels** (handled by section parser + regex): Phone, University, Company, Job Title, Projects, LinkedIn, GitHub, Portfolio, Languages.

### 2.2 Model 02 — Ranking Dataset

**Location:** `D:\cv screening\ScreenWise_IT_Datasets_ranking`

| File | Records | Purpose |
|------|---------|---------|
| `it_candidates_full.csv` | 1,500 | Candidate profiles + dimension scores |
| `it_train.csv` | 1,050 | Training split |
| `it_val.csv` | 225 | Validation split |
| `it_test.csv` | 225 | **Held-out test** |
| `it_job_descriptions.csv` | 200 | IT job postings |
| `it_candidate_job_matches.csv` | 2,000 | Candidate–job pairs with relevance labels |

**Key columns (candidates):**
- `technical_skills`, `years_experience`, `education_degree`, `projects`, `certifications`
- `score_skills`, `score_experience`, `score_education`, `score_communication`, `score_projects`, `score_certifications` (0–100)
- `overall_score` — weighted sum using IT formula below
- `label` — 1 = shortlist, 0 = reject (threshold = 60)
- `candidate_tier` — high / medium / low

**Label distribution (full set):**
- Shortlist (1): 381 candidates
- Reject (0): 1,119 candidates

**Pair relevance (matches file):**
- Relevant (1): 141 pairs
- Not relevant (0): 1,859 pairs

---

## 3. Model 01 — CV Information Extraction

### 3.1 Architecture

| Component | Description |
|-----------|-------------|
| **OCR router** | PyMuPDF (PDF), python-docx (DOCX), Tesseract (images) |
| **Gemini fallback** | Optional — triggered when extracted text is too short or low quality (`GEMINI_API_KEY`) |
| **spaCy NER** | Trained on IT dataset — 5 entity labels |
| **Section parser** | Rule-based extraction of skills, experience, education, contact fields |
| **Output** | Structured `CandidateProfile` JSON |

### 3.2 Training configuration

| Parameter | Value |
|-----------|-------|
| Algorithm | spaCy blank English + NER pipe |
| Training set | 700 records |
| Validation set | 150 records |
| Test set | 150 records (never used for training) |
| Epochs | 30 (early stopping at epoch 5, patience = 5) |
| Weak labels | 0 (IT dataset only) |
| Model output | `ai-service/models/extraction/ner_model/` |

### 3.3 Model 01 Accuracy — Before vs After

Metrics are **entity-level** precision, recall, F1, and accuracy on the **held-out test set** (150 CVs).

#### Overall performance

| Metric | Before (legacy Kaggle dataset) | After (IT test set) | Change |
|--------|-------------------------------|---------------------|--------|
| **Precision** | 0.4752 | **0.9756** | +52.0 pp |
| **Recall** | 0.2985 | **1.0000** | +70.2 pp |
| **F1-score** | 0.3667 | **0.9877** | +62.1 pp |
| **Accuracy** | 0.2245 | **0.9756** | +75.1 pp |

*Before metrics: legacy `Entity Recognition in Resumes.json` + weak labels, 164 train / 41 test.*  
*After metrics: `ScreenWise_IT_NER`, 700 train / 150 val / 150 test.*

#### Per-entity F1 (test set)

| Entity | Before F1 | After F1 | After Precision | After Recall | Test support |
|--------|-----------|----------|-----------------|--------------|--------------|
| NAME | 0.3333 | **1.0000** | 1.0000 | 1.0000 | 150 |
| EMAIL | 0.3448 | **1.0000** | 1.0000 | 1.0000 | 150 |
| SKILL | 0.4060 | **0.9965** | 0.9929 | 1.0000 | 985 |
| DEGREE | 0.1739 | **1.0000** | 1.0000 | 1.0000 | 150 |
| CERTIFICATION | — | **0.9234** | 0.8577 | 1.0000 | 205 |

*CERTIFICATION was not in the legacy model.*

#### Validation set (best epoch = 5)

| Metric | Value |
|--------|-------|
| F1 | 0.9911 |
| Precision | 0.9823 |
| Recall | 1.0000 |

**Saved to:** `ai-service/models/extraction/metrics.json`

### 3.4 Extraction fields supported at runtime

| Field | Source |
|-------|--------|
| Name, Email, Skills, Degree, Certifications | spaCy NER (trained) |
| Phone, LinkedIn, GitHub | Regex / section parser |
| Experience, Projects, Education | Section parser + NER merge |
| Communication score | Rule-based text quality proxy |

---

## 4. Model 02 — IT Candidate Ranking

### 4.1 Architecture

Model 02 is an explainable hybrid ranker with a calibrated LightGBM layer:

| Component | Description |
|-----------|-------------|
| **Embedding model** | `all-MiniLM-L6-v2` (Sentence-Transformers) — pre-trained |
| **Rule scoring** | Six IT criteria with dataset-aligned weights |
| **ML ranker** | LightGBM classifier on 16 pair features (1,382 train pairs) |
| **Fusion** | Rule score + ML probability + semantic similarity (weights tuned on val) |
| **Skill matching** | IT synonym dictionary (`js`→JavaScript, `k8s`→Kubernetes, etc.) |
| **Output** | Match %, rank, matched/missing skills, criterion breakdown, explanation |

### 4.2 IT ranking weights (aligned with dataset)

| Criterion | Weight |
|-----------|--------|
| Technical skills | 35% |
| Experience | 25% |
| Education | 15% |
| Communication | 10% |
| Projects | 10% |
| Certifications | 5% |

Shortlist threshold: **70%** (0.70 normalized score, tuned on validation set).

Calibrated fusion (saved in `models/ranking/calibration.json`):

| Parameter | Value |
|-----------|-------|
| Semantic fusion weight | 0.22 |
| LightGBM blend weight | 0.45 |
| Shortlist threshold | 0.70 |

### 4.3 Model 02 Accuracy — Before vs After

#### Candidate-level evaluation (`it_test.csv`, n = 225)

Each test candidate is scored against a representative IT job built from their profile fields.

| Metric | Before (Kaggle) | Rule-only (IT test) | **After (+ LightGBM + calibration)** |
|--------|-----------------|---------------------|--------------------------------------|
| **Precision** | 0.9024 | 0.2545 | **0.9688** |
| **Recall** | 0.5579 | 1.0000 | 0.5439 |
| **F1-score** | 0.6895 | 0.4057 | **0.6966** |
| **Accuracy** | 0.5920 | 0.2578 | **0.8800** |
| **Spearman vs gold score** | 0.2972 | **0.8255** | 0.7345 |

> **Note:** The calibrated model trades some recall (fewer false positives) for much higher precision and F1 on the imbalanced shortlist/reject labels. Spearman correlation remains strong (0.73) vs the dataset `overall_score`.

**Confusion matrix (IT test, threshold 0.70):**

| | Predicted shortlist | Predicted reject |
|--|--------------------|--------------------|
| **Actual shortlist (57)** | TP = 31 | FN = 26 |
| **Actual reject (168)** | FP = 1 | TN = 167 |

#### Pair-level evaluation (`it_candidate_job_matches.csv`, test candidates only)

252 pairs across 90 job groups where the candidate is in the held-out test split.

| Metric | Value |
|--------|-------|
| **Precision@5** | 0.4000 |
| **Recall@5** | 0.0769 |
| **MRR** | 0.2056 |
| **NDCG@5** | 0.2065 |
| Precision (pair-level, thr=0.70) | 0.3750 |
| Recall (pair-level) | 0.1154 |
| F1 (pair-level) | 0.1765 |
| Accuracy (pair-level) | 0.8889 |

Pair labels are sparse (only 7% positive), so ranking metrics (NDCG, MRR, Precision@K) are more appropriate than raw accuracy.

**Saved to:** `ai-service/models/ranking/metrics.json`

### 4.4 Ranking output fields

| Field | Description |
|-------|-------------|
| `candidate_name` | From extraction (or "Unnamed Candidate") |
| `matching_percentage` | Final fused match score (0–100) |
| `ranking_position` | Rank among candidates for the job |
| `semantic_similarity` | Sentence-Transformer cosine similarity |
| `explanation.criteria` | Per-criterion scores for radar chart |
| `explanation.matched_skills` | Skills found in both CV and job |
| `explanation.missing_skills` | Required skills not in CV |
| `explanation.strengths` / `gaps` | Human-readable summary |

---

## 5. Reproducibility Commands

### 5.1 Environment setup

```bash
# AI service
cd ai-service
pip install -r requirements.txt

# Backend
cd ../backend
npm install
npm run db:init

# Frontend
cd ../frontend
npm install
```

### 5.2 Dataset preprocessing

```bash
cd ai-service
python -m training.preprocess_it_datasets
```

### 5.3 Train Model 01 (NER)

```bash
cd ai-service
python -m training.train_ner --epochs 30 --weak-rows 0 --seed 42
```

Results written to `models/extraction/metrics.json`.

### 5.4 Evaluate Model 02 (Ranking)

```bash
cd ai-service
python -m training.train_ranker --eval-split test
```

Results written to `models/ranking/metrics.json`.

### 5.5 Run tests

```bash
cd ai-service
pytest -q
python -m evaluation.run_e2e
```

### 5.6 Run the full system

```bash
# Terminal 1 — AI service
cd ai-service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Backend
cd backend
npm run dev

# Terminal 3 — Frontend
cd frontend
npm run dev
```

Open http://localhost:5173

**Login credentials:**
- HR: `hr@cvscreening.local` / `Password123!`
- Admin: `admin@cvscreening.local` / `Password123!`

---

## 6. Configuration

Add to `ai-service/.env`:

```env
IT_NER_DATASETS_DIR=D:\cv screening\ScreenWise_IT_Datasets_ner
IT_RANKING_DATASETS_DIR=D:\cv screening\ScreenWise_IT_Datasets_ranking
GEMINI_API_KEY=          # optional — for scanned/image CV fallback
GEMINI_MODEL=gemini-1.5-flash
```

---

## 7. Limitations & Honest Notes

1. **NER high accuracy on test set** reflects structured synthetic IT CVs in the custom dataset. Real-world messy PDFs may score lower.
2. **NER covers 5 of 15 extraction fields** — phone, experience, social links rely on rules, not ML training.
3. **Ranking is imbalanced** (57 shortlist vs 168 reject in test). After LightGBM + calibration, binary F1 = **0.70** and accuracy = **88%** at threshold 0.70; Spearman = 0.73 vs `overall_score`.
4. **Pair relevance labels are sparse (7%)** — NDCG@5 (0.21) and MRR (0.21) reflect this difficulty; pair-level accuracy (89%) is inflated by negatives.
5. **No transformer/LLM trained from scratch** — embeddings use pre-trained `all-MiniLM-L6-v2`.
6. **Gemini OCR** requires a valid API key; without it, Tesseract/PyMuPDF are used.

---

## 8. Key Files Reference

| Purpose | Path |
|---------|------|
| NER metrics | `ai-service/models/extraction/metrics.json` |
| Ranking metrics | `ai-service/models/ranking/metrics.json` |
| Trained NER model | `ai-service/models/extraction/ner_model/` |
| IT weights | `ai-service/models/ranking/industry_weights.json` |
| LightGBM ranker | `ai-service/models/ranking/lgbm_ranker.pkl` |
| Calibration params | `ai-service/models/ranking/calibration.json` |
| Preprocessing script | `ai-service/training/preprocess_it_datasets.py` |
| NER training | `ai-service/training/train_ner.py` |
| Ranking evaluation | `ai-service/training/train_ranker.py` |
| Dataset report | `ai-service/datasets/processed/dataset_report.json` |
| E2E test report | `ai-service/models/e2e_report.json` |

---

## 9. Summary Table for Dissertation

| Model | Task | Algorithm | Dataset | Test F1 | Best supplementary metric |
|-------|------|-----------|---------|---------|---------------------------|
| **Model 01** | CV information extraction | spaCy NER + rules | ScreenWise IT NER (150 test) | **0.9877** | SKILL F1 = 0.9965 |
| **Model 02** | IT candidate ranking | Rule scoring + MiniLM + LightGBM (calibrated) | ScreenWise IT Ranking (225 test) | **0.6966** | Spearman = 0.7345; Precision@5 = 0.40 |

Binary F1 at calibrated threshold 0.70 on imbalanced shortlist/reject labels. Pair metrics (NDCG@5, MRR) evaluate job-specific ranking quality.
