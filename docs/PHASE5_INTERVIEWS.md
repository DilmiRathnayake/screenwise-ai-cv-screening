# Phase 5 — Interview Automation

## Purpose

After shortlisting, HR schedules interviews. The backend:

1. Persists `interviews` rows  
2. Creates `notifications`  
3. POSTs to an **n8n webhook** (`N8N_WEBHOOK_URL`) for email/calendar workflows  
4. Optionally sends email via **SendGrid** when `SENDGRID_API_KEY` is set  

Google Calendar can be wired inside n8n (recommended) or enabled later via `GOOGLE_CALENDAR_ENABLED`.

## Endpoints

| Method | Path |
|--------|------|
| GET | `/api/interviews` |
| GET | `/api/jobs/:jobId/interviews` |
| POST | `/api/interviews` |
| POST | `/api/interviews/:id/reschedule` |
| POST | `/api/interviews/:id/cancel` |
| GET | `/api/notifications` |

## n8n webhook payload (example)

```json
{
  "event": "interview.scheduled",
  "interview_id": "...",
  "candidate": { "name": "...", "email": "..." },
  "job": { "title": "..." },
  "scheduled_at": "2026-07-20T10:00:00.000Z",
  "mode": "online",
  "meeting_link": "https://meet.example.com/xyz"
}
```

Import [`docs/n8n-interview-webhook.sample.json`](n8n-interview-webhook.sample.json) as a starting workflow: Webhook → SendGrid / Gmail → Google Calendar.
