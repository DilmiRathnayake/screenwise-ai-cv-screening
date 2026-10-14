# Phase 6 — Full-Stack Deployment

One-machine Docker Compose stack for the ScreenWise research demo.

## Architecture

```
Browser → frontend (:8080 / nginx)
            └─ /api/*  proxy → backend (:5000)
                                 ├─ MySQL (:3306)
                                 └─ AI service (:8000)
```

Frontend builds with empty `VITE_API_URL` so the browser calls same-origin `/api`, proxied by nginx to the backend (no CORS friction for viva demos).

## Prerequisites

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
2. Trained NER model on the build host at `ai-service/models/extraction/ner_model/`  
   (gitignored — train with `cd ai-service && python -m training.train_ner` if missing)
3. ~4 GB free disk / ~4 GB RAM recommended (PyTorch + embeddings)

## Quick start

```bash
# From repo root
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux

# Edit .env — set a strong JWT_SECRET

docker compose up --build
```

| Service | URL |
|---------|-----|
| HR Dashboard | http://localhost:8080 |
| Backend API | http://localhost:5000 |
| AI OpenAPI | http://localhost:8000/docs |
| MySQL | localhost:3306 |

**Seed login:** `hr@cvscreening.local` / `Password123!`

First AI rank/search may take 1–2 minutes while `all-MiniLM-L6-v2` downloads into the `ai_hf_cache` volume.

## Environment

Root [`.env.example`](../.env.example) keys:

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` | **Required** — backend refuses to start in production without a real secret |
| `DB_PASSWORD` | MySQL root password (shared with backend) |
| `CORS_ORIGINS` | Allowed browser origins (default `http://localhost:8080`) |
| `PINECONE_*` / `N8N_*` / `SENDGRID_*` | Optional Phase 4–5 integrations |

## Useful commands

```bash
docker compose logs -f backend ai
docker compose down                 # stop (keeps volumes)
docker compose down -v              # wipe MySQL / uploads / vectors
DB_FORCE_RESET=true                 # set on backend to wipe schema on next init
```

## Local development (without full compose)

Still supported — three terminals as in the root README. MySQL-only: `cd backend && docker compose up -d`.

## Remote viva access (optional)

Expose the UI without cloud PaaS:

```bash
# After stack is up
npx cloudflared tunnel --url http://localhost:8080
# or: ngrok http 8080
```

Update `CORS_ORIGINS` in `.env` to the tunnel URL and restart `backend`.

## Cloud notes (optional)

Splitting across Vercel + Render is **not** recommended for this project: the AI service needs several GB RAM for torch/embeddings. Prefer Compose on a laptop or a single VM (Railway/Render Docker).

## Verify

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:5000/api/health
# Open http://localhost:8080 → login → create job → upload CV → rank → search → schedule interview
```
