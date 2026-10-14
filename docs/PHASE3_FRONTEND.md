# Phase 3 — React HR Dashboard

## Purpose

Professional HR interface for multi-industry CV screening: manage jobs, upload CVs, run AI ranking, and view explainable scores.

## API mapping

| UI action | Backend |
|-----------|---------|
| Login / Register | `POST /api/auth/login`, `/register` |
| Dashboard KPIs | `GET /api/dashboard/stats` |
| Jobs CRUD | `GET/POST/PUT/DELETE /api/jobs` |
| Close / Duplicate | `POST /api/jobs/:id/close`, `/duplicate` |
| Upload CVs | `POST /api/jobs/:jobId/cvs`, `/cvs/bulk` |
| Candidates | `GET /api/jobs/:jobId/candidates` |
| Rank | `POST /api/jobs/:jobId/rank` |
| Rankings | `GET /api/jobs/:jobId/rankings` |
| Profile drawer | `GET /api/candidates/:id` |
| Industry weights | `GET /api/ranking/weights/:industry` |

## Design notes

- Brand: **ScreenWise** (teal/ink palette, Fraunces + Source Sans 3)
- Dashboard layout with sidebar navigation
- Drag-and-drop CV upload via `react-dropzone`
- Loading / empty / toast feedback states throughout
