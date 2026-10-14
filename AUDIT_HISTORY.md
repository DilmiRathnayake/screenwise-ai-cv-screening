# Audit History

## 2026-07-17 — Full project documentation

**Scope:** Master documentation guide for dissertation / viva and developers.

### Delivered

| Area | Path |
|------|------|
| Master guide | `docs/DOCUMENTATION.md` |
| Docs index | `docs/README.md` |
| Root README | Links to full docs hub |

Covers architecture, setup, env, schema, AI/backend/frontend APIs, workflows, metrics, deploy, troubleshooting.

## 2026-07-17 — Frontend Premium SaaS Redesign

**Scope:** Frontend-only redesign (no backend / AI / DB / API changes).

### Delivered

| Area | Note |
|------|------|
| Design system | Radix + CVA components, glass tokens, light/dark/system theme |
| Landing | Animated marketing page at `/` |
| Auth portals | Admin / HR (live API) + Candidate demo; forgot/OTP UI demos |
| HR app | `/hr/*` — dashboard, jobs (grid/list/kanban), job detail + AI ranking, search, FullCalendar interviews, reports, notifications, settings |
| Admin app | `/admin/*` — command center, health, people overview + shared modules |
| Candidate | `/candidate/*` mock dashboard |
| Charts | Recharts (replaced Chart.js) |
| Toasts | react-hot-toast |

### UX / findings

| Area | Note | Severity |
|------|------|----------|
| Candidate / OTP / Google sync | Demo-only — labeled in UI | Info |
| Admin infra gauges | Mock CPU/memory/storage/API | Info |
| Bundle size | ~1.4MB JS — FullCalendar + Recharts; code-split later | Low |
| Backend contract | Unchanged; existing endpoints only | Info |

## 2026-07-17 — Phase 6: Full-Stack Docker Deploy

**Scope:** One-command demo stack (MySQL + AI + Express + nginx frontend) and production wiring.

### Delivered

| Area | Path / note |
|------|-------------|
| Root compose | `docker-compose.yml` — mysql, ai, backend, frontend |
| Dockerfiles | `ai-service/`, `backend/`, `frontend/` (+ nginx `/api` proxy) |
| Entrypoint | `backend/docker-entrypoint.sh` — wait MySQL → idempotent `db:init` → start |
| Env | Root `.env.example`; `JWT_SECRET` required when `NODE_ENV=production` |
| Frontend API | Same-origin default (`VITE_API_URL=""`) for nginx proxy |
| Docs | `docs/PHASE6_DEPLOY.md` |

### Findings / Notes

| Area | Note | Severity |
|------|------|----------|
| Docker Desktop | Required for compose; if missing on host, use local 3-terminal dev | Warning |
| NER in image | `ner_model` gitignored — must exist on build host | Warning |
| HF download | First embedding call downloads MiniLM into volume | Info |
| Free PaaS | Torch RAM unfit for free serverless; prefer Compose/VM | Info |
| Smoke (local) | health→login→job→upload→rank→search→interview **PASSED** (Docker Desktop not installed on build host) | Info |

## 2026-07-17 — Phases 4 & 5: Semantic Search + Interview Automation

**Scope:** RAG candidate search (Pinecone or local NPZ) and interview scheduling with n8n/SendGrid hooks.

### Delivered

| Area | Note |
|------|------|
| AI upsert/search | `POST /api/v1/embeddings/upsert`, `POST /api/v1/search` |
| Local vector fallback | Works without Pinecone API key |
| Backend search | `POST /api/search`, auto-index on CV upload, `POST /api/search/sync` |
| Interviews table | Migration `sql/migration_phase4_5.sql` |
| Interview APIs | schedule / reschedule / cancel + notifications |
| n8n | Webhook payload + sample workflow JSON |
| Frontend | `/search`, `/interviews` nav pages |

### Findings / Notes

| Area | Note | Severity |
|------|------|----------|
| Pinecone | Optional — set `PINECONE_API_KEY` for cloud index | Info |
| n8n / SendGrid | Optional env vars; scheduling works offline without them | Info |
| Google Calendar | Delegated to n8n workflow (recommended for research demo) | Info |

## 2026-07-17 — Phase 3: React HR Dashboard Complete

**Scope:** Vite/React frontend with Tailwind, TanStack Query, React Hook Form, Framer Motion, Chart.js; dashboard stats endpoint on backend.

### Delivered

| Area | Path / note |
|------|-------------|
| Frontend app | `frontend/` — login, register, dashboard, jobs, job detail |
| CV upload UI | Drag-and-drop single/bulk via react-dropzone |
| Ranking UI | Run AI rank + expandable criterion explanations |
| Dashboard API | `GET /api/dashboard/stats` in backend |
| Docs | `frontend/README.md`, `docs/PHASE3_FRONTEND.md` |

### Findings / Notes

| Area | Note | Severity |
|------|------|----------|
| Bundle size | Production chunk ~717KB — acceptable for MVP; code-split later | Low |
| Auth storage | JWT in localStorage — fine for research demo; harden for production | Medium |
| Design | ScreenWise teal/ink brand; Fraunces + Source Sans 3 | Info |

## 2026-07-17 — Phase 2: Backend API Complete

**Scope:** Node.js/Express MVC backend with JWT auth, normalized MySQL schema, Multer CV upload, and AI service client for extract/rank.

### Delivered

| Area | Path / note |
|------|-------------|
| Express MVC | `backend/src/` controllers, services, repositories, routes, middlewares |
| MySQL DDL | `backend/sql/schema.sql` + seed via `npm run db:init` |
| Auth | JWT register/login/me; roles admin/hr; bcrypt |
| Jobs | CRUD, close, duplicate; industry weights from AI |
| CV upload | Single + bulk → AI extract → candidates/applications |
| Ranking | `POST /api/jobs/:jobId/rank` → `ranking_results` + shortlist |
| Health | DB ping + AI `/api/v1/health` |
| Docs | `backend/README.md`, `docs/PHASE2_BACKEND.md` |
| Docker MySQL | `backend/docker-compose.yml` (local MySQL not installed on this machine) |

### Findings / Notes

| Area | Note | Severity |
|------|------|----------|
| MySQL | No local MySQL/Docker on build host — schema + init script ready; user must start DB | Warning |
| Multer 1.x | npm warns to upgrade to 2.x — functional for Phase 2; upgrade in hardening pass | Low |
| Admin job create | Admins without `hr_managers` row cannot create jobs (by design) | Info |

### Security notes

- Passwords hashed with bcrypt; JWT required for mutating routes
- File type whitelist + size limit aligned with AI service
- Errors sanitized in production via `NODE_ENV=production`

## 2026-07-17 — Phase 1: AI Models Complete

**Scope:** CV Extraction Model (OCR + NLP/NER) and Candidate Ranking Model (Sentence-Transformers + industry-weighted scoring).

### Model metrics (dissertation baseline)

| Model | Metric | Value | Notes |
|-------|--------|------:|-------|
| Extraction NER | Precision | 0.445 | spaCy blank NER, 25 epochs, 164 train / 41 test |
| Extraction NER | Recall | 0.432 | Exact-span entity match (strict) |
| Extraction NER | F1 | 0.439 | Skills F1 ~0.50; contact fields boosted by rules |
| Ranking | Hire/Reject Precision | 0.902 | AI_Resume_Screening.csv (n=1000) |
| Ranking | Hire/Reject F1 | 0.690 | Median-threshold binary decision |
| Ranking | Spearman vs AI Score | 0.297 | Positive correlation |
| Ranking | NDCG@10 | 0.808 | resume_data.csv sample n=200 |

### Findings / Notes

| Area | Note | Severity |
|------|------|----------|
| NER data size | 220 annotated resumes; span misalignment common in Kaggle JSON | Medium |
| Communication score | Rule-based proxy (readability/structure) — no labeled dataset | Medium |
| Tesseract | Not installed on this machine — image OCR disabled until system install | Warning |
| Email cleaning | Fixed `@mention` regex that previously destroyed emails | Fixed |
| Section-aware embeddings | Implemented as planned improvement for ranking | Info |

### Actions Taken

- Scaffolded FastAPI MVC AI service under `ai-service/`
- Implemented OCR router (PyMuPDF / python-docx / Tesseract+Pillow)
- Trained spaCy NER; dual extraction with section parser
- Implemented industry-weighted ranking + Sentence-Transformers
- Tests: 9 passed; e2e extract→rank report in `models/e2e_report.json`
- Deferred Node/React/MySQL/Pinecone/n8n to later phases

## 2026-07-17 — Phase 1: AI Models Scaffold

**Scope:** Initial scaffold and configuration.

## 2026-09-15 — ScreenWise IT Dataset Integration

**Scope:** IT-only dataset training, OCR/Gemini fallback, ranking calibration, API/frontend fixes.

### Dataset findings

| Dataset | Records | Notes |
|---------|---------|-------|
| IT NER (`it_ner_*.json`) | 1000 (700/150/150 split) | 5 labels: NAME, EMAIL, SKILL, DEGREE, CERTIFICATION; 0 duplicate texts |
| IT candidates | 1500 (1050/225/225 split) | Shortlist label threshold 60; imbalanced 381/1119 |
| IT job matches | 2000 pairs | relevance_label 141 positive; 325 test-candidate pairs |

### Model metrics (held-out test)

| Model | Before | After |
|-------|--------|-------|
| NER F1 | 0.3667 | **0.9877** (150 test docs) |
| Ranking Spearman vs overall_score | 0.2972 (Kaggle) | **0.8255** (225 IT test candidates) |
| Pair NDCG@5 | N/A | 0.2109 (252 test pairs) |

### Changes

- Preprocessing: `training/preprocess_it_datasets.py` → `datasets/processed/`
- NER retrained on IT JSON; CERTIFICATION wired to extraction
- Gemini OCR fallback (`GEMINI_API_KEY`); Tesseract/PyMuPDF preserved
- IT-only ranking weights (35/25/15/10/10/5)
- Backend: `candidate_name`, structured `explanation`, Unnamed Candidate fallback
- Frontend: real ranking bar chart, criterion_scores mapping, no synthetic radar data

### Tests

- `pytest -q`: 9 passed
- `python -m evaluation.run_e2e`: extract + rank OK

---

## 2026-09-15 — Model 02 accuracy improvement (LightGBM + calibration)

**Scope:** Train and integrate LightGBM pair ranker; validation calibration; IT skill synonyms.

### Model 02 metrics (held-out IT test, n=225 candidates)

| Metric | Before | After |
|--------|--------|-------|
| Binary F1 (thr=0.70) | 0.4057 (thr=0.60) | **0.6966** |
| Precision | 0.2545 | **0.9688** |
| Accuracy | 0.2578 | **0.8800** |
| Spearman vs overall_score | 0.8255 | 0.7345 |
| Pair NDCG@5 | 0.2109 | 0.2065 |

### Delivered

- `app/utils/it_skills.py` — IT synonym normalization
- `app/services/ranking_features.py` — 16-feature vector for LightGBM
- `app/repositories/ranker_repository.py` — loads `lgbm_ranker.pkl` + `calibration.json`
- `training/train_ranker.py` — train LGBM on 1,382 train pairs, calibrate on val, evaluate test
- Artifacts: `models/ranking/lgbm_ranker.pkl`, `calibration.json` (semantic=0.22, ml_blend=0.45, threshold=0.70)

### Tests

- `pytest tests/test_core.py -q`: 9 passed

---

## 2026-09-16 — Model 2 IT LambdaMART pipeline + UI metrics wiring

**Scope:** `model2_it/` dataset pipeline (prepare → train → evaluate); real Kaggle resume hook; frontend Model 2 metrics from held-out test JSON.

### Delivered

| Artifact | Path |
|----------|------|
| Feature engineering | `model2_it/prepare_model2_features.py` |
| LambdaMART training | `model2_it/train_model2.py` |
| Test evaluation | `model2_it/evaluate_model2.py` |
| Metrics API | `GET /api/v1/ranking/model2/metrics` (ai-service) → backend proxy |
| UI | `LandingPage.jsx` — NDCG@5 from `evaluation/model2_metrics.json` |

### Model 2 test metrics (held-out, 101 jobs / 1,416 pairs)

| Metric | ML model | Skill-overlap baseline |
|--------|----------|------------------------|
| NDCG@5 | 0.9989 | 0.9761 |
| NDCG@10 | 0.9997 | 0.9832 |
| MRR | 1.0 | 1.0 |
| Precision@5 | 0.8634 | 0.8376 |
| Recall@5 | 0.8003 | 0.7755 |
| Spearman | 0.9539 | 0.9032 |
| Kendall τ | 0.8456 | 0.7973 |

*High scores reflect recovery of the synthetic rubric, not real recruiter accuracy.*

### Technical debt (review checklist)

| File/Symbol | Category | Reason safe to remove | Risk |
|-------------|----------|----------------------|------|
| `LandingPage` old 90% stat | Stale demo value | Replaced by API-driven NDCG@5 | Low |
| `AdminPages` `DEMO_GAUGES` | Stale logs/demo | Infrastructure mock, not Model 2 | Low — Model 1/admin scope |

## 2026-09-16 — Candidate portal: live API (no demo)

**Scope:** Replace mock candidate dashboard with real backend auth + data linked by email.

### Delivered

| Area | Path / endpoint |
|------|-----------------|
| DB role | `users.role` includes `candidate`; migration in `initDb.js` |
| Seed login | `candidate@cvscreening.local` / `Password123!` |
| API | `GET /api/candidate/dashboard`, `/applications`, `/interviews`, `/profile` |
| Service | `backend/src/services/candidateService.js` |
| Frontend | `CandidatePages.jsx` — React Query; demo banner removed |
| Register | `/register/candidate` |

### Data linking

Applications and interviews match `users.email` ↔ `candidates.email` from HR CV uploads. Job recommendations rank the candidate profile against active jobs not yet applied to (AI ranker with skill fallback).

### Removed

| File/Symbol | Category | Reason safe to remove | Risk |
|-------------|----------|----------------------|------|
| `frontend/src/demo/candidateStore.js` | Orphaned file | Replaced by API | None |
| `startDemoCandidate()` | Dead code | Removed from `authStore.js` | None |
