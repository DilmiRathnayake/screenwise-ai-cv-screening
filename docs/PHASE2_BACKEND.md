# Phase 2 — Backend API

## Purpose

Enterprise Node.js layer that owns authentication, job vacancies, CV ingestion, and persistence, while delegating extraction/ranking to the Phase 1 AI service.

## Modules

1. **Auth** — JWT login/register, roles `admin` | `hr`, bcrypt passwords  
2. **Jobs** — CRUD, close, duplicate; industry ranking weights from AI defaults  
3. **CV Upload** — Multer single/bulk → AI extract → candidates + applications  
4. **Ranking** — AI rank → `ranking_results` + shortlist status  
5. **Health** — MySQL ping + AI `/api/v1/health`

## Data flow

```
HR JWT → POST /api/jobs/:id/cvs
       → Multer disk store
       → AiServiceClient.extract
       → candidates + candidate_skills + applications + cv_files

HR JWT → POST /api/jobs/:id/rank
       → load applications
       → AiServiceClient.rank
       → ranking_results + shortlisted status
```

## MySQL tables

`users`, `hr_managers`, `jobs`, `skills`, `job_skills`, `candidates`, `candidate_skills`, `cv_files`, `applications`, `ranking_results`, `notifications` (stub).

See `backend/sql/schema.sql`.
