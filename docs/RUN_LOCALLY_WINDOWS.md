# Run ScreenWise locally on Windows (no Docker)

Docker files exist in the repository but are **optional and not needed** for any step below.

## Services and ports (taken from the project configuration)

| Service | Folder | Default port | Config file |
|---------|--------|--------------|-------------|
| MySQL | (installed on Windows) | 3306 | `backend/.env` → `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` |
| AI service (FastAPI) | `ai-service/` | 8000 | `ai-service/.env` |
| Backend (Express) | `backend/` | 5000 | `backend/.env` → `PORT`, `AI_SERVICE_URL`, `CORS_ORIGINS` |
| Frontend (Vite) | `frontend/` | 5173 | `frontend/.env` → `VITE_API_URL` |

**All four must run at the same time** for the full application (open four terminals). Start order: MySQL → AI service → backend → frontend.
The Jupyter demo only needs the Python environment (the AI service does not have to be running).

Prerequisites: Node.js 18+, Python **3.10 or newer**, MySQL 8 (or MariaDB). Tesseract OCR is optional (only for image CVs).

Never commit or share `.env` files; they are git-ignored. Keep API keys out of documents and screenshots.

---

## 1. MySQL and database preparation

1. Start MySQL (Services → *MySQL80* → Start, or `net start MySQL80` in an Administrator terminal).
2. Create `backend\.env` from your existing one. The variables used are (values are examples only):

   ```
   PORT=5000
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=<your MySQL password, empty if none>
   DB_NAME=cv_screening
   JWT_SECRET=<any long random string>
   AI_SERVICE_URL=http://localhost:8000
   CORS_ORIGINS=http://localhost:5173
   ```

3. Create the schema and the three demo accounts (admin, HR, candidate):

   ```bat
   cd backend
   npm install
   npm run db:init
   ```

   `db:init` creates the `cv_screening` database and seeds `admin@cvscreening.local`, `hr@cvscreening.local` and
   `candidate@cvscreening.local` (demo password printed by the script). It is safe to re-run; it only wipes data if you set `DB_FORCE_RESET=true`.

   The script uses the database name `cv_screening` internally, so keep `DB_NAME=cv_screening`.

Check: `mysql -u root -p -e "SELECT email, role FROM cv_screening.users"` lists the three accounts.

## 2. AI service (Python / FastAPI)

```bat
cd ai-service
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

* **Run it from the `ai-service` folder.** Model paths in `ai-service\.env` (for example `NER_MODEL_PATH=models/extraction/ner_model`) are relative to the working directory.
* The first start downloads the `all-MiniLM-L6-v2` embedding model (~90 MB) if it is not cached.
* `ai-service\.env` also contains Windows dataset paths (`DATASETS_DIR`, `IT_NER_DATASETS_DIR`, `IT_RANKING_DATASETS_DIR`). They are **only needed for retraining**; at run time the
  service uses the copies in `ai-service\datasets\processed\`. Update them if your folders are elsewhere.
* Optional keys (`GEMINI_API_KEY`, `PINECONE_API_KEY`) can stay empty: Gemini OCR fallback is skipped and a local vector store is used.
* The trained NER model (`models\extraction\ner_model`) and the LightGBM blend file (`models\ranking\lgbm_ranker.pkl`) are git-ignored. If they are missing the service still starts, logs a warning, and uses rule-based extraction / scoring. `GET /api/v1/health` reports `ner_model_loaded`.

Check: open <http://localhost:8000/api/v1/health> → `{"status":"ok", ...}`; interactive docs at <http://localhost:8000/docs>.

## 3. Backend (Node.js / Express)

```bat
cd backend
npm install
npm start
```

(`npm run dev` restarts on file changes.)

Check: <http://localhost:5000/api/health> → `database.ok: true` and `ai.ok: true` (the AI part is `false` if step 2 is not running).

## 4. Frontend (React / Vite)

```bat
cd frontend
npm install
npm run dev
```

If `npm ci` complains that `package-lock.json` is out of sync, use `npm install` instead (this is a known optional-dependency lockfile quirk).

`frontend\.env` – `VITE_API_URL` may be left **empty** (the Vite dev server proxies `/api` to `http://localhost:5000`) or set to `http://localhost:5000`. If you open the app from a different origin, add that origin to `CORS_ORIGINS` in `backend\.env`.

Open <http://localhost:5173>. Portals: `/login/hr`, `/login/admin`, `/login/candidate`. All three call the real backend `/api/auth/login`; the candidate dashboard reads real data from `/api/candidate/*`
(only the *forgot password / OTP* screens are UI-only demos).

If you ever see a blank page after testing: clear the site's local storage (DevTools → Application → Local Storage → delete `cv_screening_token` and `cv_screening_user`) and reload.
The application now clears such stale sessions automatically.

## 5. Jupyter Notebook (AI demonstration)

```bat
cd ai-service
.venv\Scripts\activate
pip install jupyter ipykernel
python -m ipykernel install --user --name screenwise --display-name "ScreenWise (ai-service)"
jupyter notebook notebooks\ScreenWise_AI_Demonstration.ipynb
```

Choose the kernel **ScreenWise (ai-service)**, then *Kernel → Restart & Run All*. The notebook locates the repository automatically and does not need Docker, the database or the other services
(an optional cell uses the live AI service if it happens to be running on port 8000). It blanks the Gemini/Pinecone keys for its own process, so no cloud API is called.

---

## Health checklist

| Check | Expected |
|-------|----------|
| <http://localhost:8000/api/v1/health> | `status: ok` |
| <http://localhost:5000/api/health> | `database.ok: true`, `ai.ok: true` |
| <http://localhost:5173/login/hr> | login form; sign in goes to `/hr` |
| <http://localhost:5173/login/admin> | sign in goes to `/admin` |
| <http://localhost:5173/login/candidate> | sign in goes to `/candidate` |
| Wrong password | message "Invalid email or password" (no blank page) |
| Backend stopped | message "Cannot reach the server. Please check that the backend is running." |

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `ECONNREFUSED 3306` / `database.ok: false` | MySQL not started, or wrong `DB_*` values in `backend\.env` |
| `ai.ok: false` in backend health | AI service not running on the URL in `AI_SERVICE_URL` |
| CORS error in browser console | add the page origin to `CORS_ORIGINS` and restart the backend |
| `ModuleNotFoundError` in the AI service | virtual environment not activated, or `pip install -r requirements.txt` not run in `ai-service` |
| `TypeError: unsupported operand type(s) for |` | Python older than 3.10 |
| Image CVs fail | install Tesseract and set `TESSERACT_CMD` in `ai-service\.env` |
