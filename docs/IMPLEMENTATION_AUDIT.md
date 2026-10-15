# Implementation audit — report vs repository

Date: 2026-10-15 · Branch `main` · Report audited: `Final_Project_Report_2636708.docx` (the original is untouched).
Everything below was checked in the code or by running it on macOS with MySQL, the AI service, the backend and the frontend running locally.
Statuses: **verified**, **partially implemented**, **not verified**, **missing**, **unsupported by available evidence**.

## 1. Requirements matrix

| Requirement | Report claim | Existing implementation | Evidence | Status | Required action |
|---|---|---|---|---|---|
| FR1 | Candidates upload a CV in PDF, DOCX or image | HR uploads CVs to a job (`POST /api/jobs/:id/cvs`, `/cvs/bulk`). Allowed: `.pdf .docx .png .jpg .jpeg`, 25 MB limit. The Candidate portal is read-only (dashboard, applications, interviews, profile); there is **no candidate self-upload route**. | PDF and DOCX uploads returned 201; `.txt` returned 400 "Unsupported file type"; no-auth returned 401; bulk of 2 files returned 201. Image upload and the 25 MB limit were not exercised. | Partially implemented | Reword FR1 to "HR uploads CVs on behalf of candidates", or build a candidate upload (not done, new feature) |
| FR2 | Text via OCR (scans/images) or direct extraction (digital files) | `OCRService`: PyMuPDF for PDF, python-docx for DOCX, Tesseract for images, optional Gemini fallback. | 100 of 100 sampled dataset PDFs gave readable text; DOCX verified. **Tesseract is not installed on the test machine, so image OCR is not verified.** | Partially implemented (digital files verified, OCR not) | Test image OCR on a machine with Tesseract |
| FR3 | NLP extraction of skills, education, experience, projects, certifications, communication score | `ExtractionService`: section parser + spaCy NER (if model present) + `communication_score`. All fields returned and stored. | Synthetic PDF and DOCX gave name, email, skills, certifications and a communication score through the API; data persisted and returned by `GET /candidates`. On 100 real-style CVs the rule-only pipeline found no education in 77 and no experience in 62. The **trained NER model folder is not in the repository** (git-ignored). | Partially implemented / verified without NER | Copy `ai-service/models/extraction/ner_model/` from the dev machine; state the rule-only limitation |
| FR4 | Embeddings stored in Pinecone, natural-language semantic search | `VectorStore`: Pinecone if `PINECONE_API_KEY` is set, otherwise a local NPZ index. `/api/search/sync` and `/api/search` exist. | Local backend: sync indexed 6 of 6, search returned ranked hits in 155 ms. **Pinecone not tested** (cloud call; key deliberately blanked). | Partially implemented (local verified, Pinecone not verified) | Test with the real key on the dev machine |
| FR5 | Six-dimension IT-calibrated weighted ranking | Weights 35/25/15/10/10/5 (skills, experience, education, communication, projects, certifications) in code, API and `calibration.json`. Plus MiniLM similarity fusion. | `GET /api/v1/ranking/weights/it` returns those weights; ranking order and explanations verified (Asha 53% > Kamal 25% > Nuwan 16% on three synthetic CVs). **LightGBM blend not active here** (`lgbm_ranker.pkl` absent). | Verified (rules + embeddings); LightGBM layer not verified | Copy `ai-service/models/ranking/lgbm_ranker.pkl` from the dev machine |
| FR6 | HR creates vacancies, views ranked lists on a dashboard | Jobs CRUD, ranking, dashboard stats, ranked list UI. | Job create (201), validation (400 for missing title), rank (200), rankings persisted and shown in the UI. | Verified | None |
| FR7 | Auto-schedule and send interview invitations via n8n after shortlisting | `interviewService` posts to `N8N_WEBHOOK_URL` and SendGrid/Google if configured; skipped if not configured. | Code reviewed. **Not executed**: your `.env` points at real n8n/SendGrid/Google services and a test would send real webhooks and emails. | Not verified | Test on the dev machine with a throw-away email and the n8n execution log as evidence |
| FR8 | Filter and compare candidates side-by-side | **Was missing.** The ranking tab had no filter and no compare. Added in this work: minimum-score filter, shortlisted-only filter, and a side-by-side table for 2 to 3 candidates (client-side only, no API or database change). | Browser test: filter at 50% showed 1 of 3 (53%, others 25% and 16%); comparing two candidates showed all six criteria plus overall match. | Verified (implemented now) | The report's TC09 must be re-executed and its screenshots added (see Section 4) |
| NFR1 | Usability | Consistent layout, light/dark theme, clear error messages. | No usability study was run. | Unsupported by available evidence | Use a short task-based check with 3 to 5 people, or reword as a design intent |
| NFR2 | Search within a few seconds | Local search: 155 ms on a 6-vector index (first sync 13.7 s including model load). | Pinecone and larger pools not tested. | Partially verified (tiny pool, local only) | Quote it only for a small pool |
| NFR3 | Parameterised queries and role-based access control | All SQL uses `?` placeholders (the dynamic `IN (...)` list is built only from `?`). `authenticate` + `authorize` on routes. bcrypt hashing, JWT. | Matrix: no token 401; garbage token 401; candidate on HR API 403; HR on candidate API 403; admin 200; anonymous `role=admin` register 403; SQL-injection-style login input 400. SQL checked by code search, not a full audit. | Verified | Set a strong `JWT_SECRET` in `backend/.env` (the current value is a placeholder) |
| NFR4 | Scalability (MySQL and Pinecone separate) | Separate stores by design. | No load test. | Unsupported by available evidence | Describe as design, not as a measured result |
| NFR5 | Fairness: outcomes auditable across demographic groups | Six weights are visible and each candidate has an explanation. No demographic data is collected and no bias audit exists in the code. | Code search found nothing. Your report's Section 7.4 itself says a full fairness audit was not possible. | Partially implemented (transparency only) | Reword NFR5 as "explainability", not "auditable across demographic groups" |

## 2. Which models the live application actually uses

| Component | Present in repo? | Used by the live API? | Notes |
|---|---|---|---|
| spaCy NER (Model 01) | **No** (`models/extraction/ner_model/` is git-ignored) | Yes if present, otherwise the service logs a warning and runs rule-only | `/api/v1/health` shows `ner_model_loaded`. `models/e2e_report.json` shows `ner_loaded: true` on the dev machine, so it existed there. Stored metrics: `models/extraction/metrics.json`. |
| Rule-based section parser | Yes | Yes | Fixed to recognise `SOFT SKILLS` and `WORK EXPERIENCE` headings (precision 0.47 to 0.97 on the 150 synthetic test CVs). |
| Weighted six-criterion scoring | Yes | Yes | |
| MiniLM sentence embeddings | Downloaded on first use from Hugging Face | Yes (fusion weight 0.08) | Needs network once. |
| LightGBM calibrated blend (report's Model 02 "ML layer") | **No** (`lgbm_ranker.pkl` is git-ignored) | Only if the file exists and `ml_blend_weight > 0` | Calibration file says 0.25. Without the file, live ranking = rules + embeddings. |
| LightGBM LambdaMART (`model2_it/`) | Yes (booster loads and re-scores its test file) | **No** | A separate research artefact. **Not mentioned in the report.** Its near-perfect metrics (NDCG@5 0.9997) should not be presented as the system's ranking accuracy. |

No model was trained, fine-tuned or overwritten in this work.

## 3. Report numbers vs what is in the repository

1. **Model 02 table (report Table 6.3): F1 0.6966, accuracy 88%, threshold 0.70.** These match an *older* run stored inside `models/ranking/metrics.json` (nested under `baseline.baseline`, calibration semantic 0.22, ML blend 0.45, threshold 0.70).
   The **current** `calibration.json` is semantic 0.08, ML blend 0.25, threshold 0.60, and the current top-level metrics in the same file differ (accuracy 0.9956, F1 0.9912, validation F1 1.0).
   So the deployed calibration is not the one the report's numbers came from. Decide which is correct and say so in the viva; do not change either silently.
2. **NER training epochs.** Report says best epoch 5; `models/extraction/metrics.json` says 15 epochs, best epoch 7; `docs/IT_DATASET_AND_MODELS.md` says 30 epochs, early stop at 5. Pick one source.
3. **`docs/PROJECT_REPORT.md`** (a guide inside the repo, not the submitted report) says "combined ≈ 98.8%" (average of unlike metrics) and Model 2 top-1 100%, both of which differ from the submitted report. Do not quote it.
4. **TC09 (filter and compare) is marked Pass in the report**, but its "Executed Date" and "Actual Result" fields are blank and the feature did not exist in the UI until now.
   Chapter 6 itself says evidence exists for only four of the test cases. Re-run TC09 against the new feature and add real screenshots, or mark it "not executed".
5. **Legacy Kaggle files** used for the report's "Before" figures (`resume_data.csv`, `AI_Resume_Screening.csv`, `Entity Recognition in Resumes.json`) are not in the repository. The "Before" numbers cannot be reproduced here.
6. **Settings paths.** `ai-service/.env` points at `F:\CINEC\...`; the code falls back to the committed copies in `ai-service/datasets/processed/`, so the service runs on any machine. Only retraining would need the original folders.

## 4. Defects and findings

| Item | Severity | Status |
|---|---|---|
| Blank page on login (stale token without a valid user caused a redirect loop) | High | Fixed earlier (`frontend/src/store/authStore.js`) |
| Section parser did not recognise `SOFT SKILLS` / `WORK EXPERIENCE` | Medium | Fixed earlier (`section_parser.py`) |
| FR8 filter/compare missing | Medium | Fixed now (`frontend/src/pages/workspace/JobDetailPage.jsx`) |
| Empty or corrupt PDF returns HTTP 502 with a clear message; the failure is recorded as `failed` in the database | Low | Left as is (message is clear; only the status code is loose) |
| Re-uploading a CV with the same email to the same job creates a duplicate application, so the candidate is ranked twice | Low to medium | **Not fixed.** Changing it alters application persistence. De-duplicate in the repository layer if required. |
| `CI/CD` is split into `CI` and `CD` by the skill tokenizer | Low | Not fixed |
| Backend `npm test` does not exit by itself once the real database exists (the connection pool stays open) | Low | Not fixed (test harness only) |
| `.env` files contain real keys (SendGrid, Google, Gemini, Pinecone) | Security | Not in Git. Rotate if the folder was ever shared. |
| The new dataset contains real personal data and is committed to a public repository | Privacy | Needs your decision (see `DATASET_AUDIT.md`) |

## 5. Tests run (macOS, local)

| Area | Result |
|---|---|
| Backend unit/smoke tests | 6 of 6 pass |
| AI service pytest | 9 of 9 pass (before and after the parser change) |
| Frontend lint / build | Build passes; lint shows warnings only, none in the new code |
| Auth: HR, Admin, Candidate login; wrong password; expired session; refresh of protected page | Verified in the browser and API |
| Protected API access and role boundaries | Verified (Section 1, NFR3) |
| Job create, validation, PDF/DOCX upload, bulk upload, invalid type, empty and corrupt file | Verified |
| Extraction and ranking through the backend, persistence, ranking explanation | Verified |
| AI service stopped: upload and rank return clear 502 messages, health shows `ai.ok: false`, other routes keep working | Verified |
| Semantic search (local vector store) | Verified |
| New filter and compare (FR8) in the browser | Verified |
| Pinecone, n8n/SendGrid/Google Calendar, image OCR, trained NER, LightGBM blend, Windows | **Not tested** |

## 6. Wording that is safe to use in the viva

- "Extraction is OCR or direct text reading, then a rule-based section parser and, when its model file is present, a spaCy NER model."
- "Ranking is a six-criterion weighted score fused with sentence-embedding similarity, with an optional calibrated LightGBM layer."
- "All datasets used for training and evaluation are synthetic, so the metrics show agreement with the dataset rules, not real hiring accuracy."
- "The extra annotated resume dataset is real-looking but has a single generic label type with noisy and overlapping spans, so I used it only to test the pipeline's robustness."
