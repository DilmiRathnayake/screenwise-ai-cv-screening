'use strict';

const { v4: uuidv4 } = require('uuid');
const axios = require('axios');
const { query } = require('../config/db');
const config = require('../config');
const logger = require('../utils/logger');
const { AppError } = require('../middlewares/errorHandler');

async function createNotification({ userId, candidateId, type, title, body }) {
  const id = uuidv4();
  await query(
    `INSERT INTO notifications (id, user_id, candidate_id, type, title, body)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [id, userId || null, candidateId || null, type, title, body || null]
  );
  return id;
}

async function triggerN8n(payload) {
  const url = config.n8n?.webhookUrl;
  if (!url) {
    logger.info('n8n webhook not configured — skipping external automation');
    return { sent: false, reason: 'N8N_WEBHOOK_URL not set' };
  }
  try {
    const { data } = await axios.post(url, payload, { timeout: 15000 });
    return { sent: true, response: data };
  } catch (err) {
    logger.warn(`n8n webhook failed: ${err.message}`);
    return { sent: false, reason: err.message };
  }
}

async function scheduleInterview(input, user) {
  const {
    applicationId,
    scheduledAt,
    durationMinutes = 45,
    mode = 'online',
    meetingLink,
    location,
    notes,
  } = input;

  const apps = await query(
    `SELECT a.id, a.job_id, a.candidate_id, a.status,
            c.full_name, c.email, j.title AS job_title, j.hr_manager_id
     FROM applications a
     JOIN candidates c ON c.id = a.candidate_id
     JOIN jobs j ON j.id = a.job_id
     WHERE a.id = ?
     LIMIT 1`,
    [applicationId]
  );
  const app = apps[0];
  if (!app) throw new AppError('Application not found', 404);
  if (user.role !== 'admin' && app.hr_manager_id !== user.hr_manager_id) {
    throw new AppError('Forbidden', 403);
  }

  const id = uuidv4();
  await query(
    `INSERT INTO interviews (
      id, application_id, job_id, candidate_id, scheduled_at, duration_minutes,
      mode, meeting_link, location, status, notes, created_by
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?)`,
    [
      id,
      applicationId,
      app.job_id,
      app.candidate_id,
      new Date(scheduledAt),
      durationMinutes,
      mode,
      meetingLink || null,
      location || null,
      notes || null,
      user.id,
    ]
  );

  await query(
    `UPDATE applications SET status = 'shortlisted' WHERE id = ?`,
    [applicationId]
  );

  const n8nPayload = {
    event: 'interview.scheduled',
    interview_id: id,
    candidate: { id: app.candidate_id, name: app.full_name, email: app.email },
    job: { id: app.job_id, title: app.job_title },
    scheduled_at: scheduledAt,
    duration_minutes: durationMinutes,
    mode,
    meeting_link: meetingLink,
    location,
    sendgrid_enabled: Boolean(config.sendgrid?.apiKey),
    google_calendar_enabled: Boolean(config.google?.calendarEnabled),
  };

  const n8n = await triggerN8n(n8nPayload);

  await createNotification({
    userId: user.id,
    candidateId: app.candidate_id,
    type: 'interview_scheduled',
    title: `Interview scheduled: ${app.full_name}`,
    body: `${app.job_title} at ${scheduledAt}`,
  });

  // Optional SendGrid direct send (when configured)
  if (config.sendgrid?.apiKey && app.email) {
    try {
      await axios.post(
        'https://api.sendgrid.com/v3/mail/send',
        {
          personalizations: [{ to: [{ email: app.email }] }],
          from: {
            email: config.sendgrid.fromEmail || 'noreply@cvscreening.local',
          },
          subject: `Interview invitation — ${app.job_title}`,
          content: [
            {
              type: 'text/plain',
              value: `Hello ${app.full_name || 'Candidate'},\n\nYou are invited to interview for ${app.job_title} on ${scheduledAt}.\nMode: ${mode}\n${meetingLink ? `Link: ${meetingLink}\n` : ''}\nRegards,\nScreenWise HR`,
            },
          ],
        },
        {
          headers: {
            Authorization: `Bearer ${config.sendgrid.apiKey}`,
            'Content-Type': 'application/json',
          },
          timeout: 15000,
          validateStatus: () => true,
        }
      );
    } catch (err) {
      logger.warn(`SendGrid email failed: ${err.message}`);
    }
  }

  const interview = await getById(id);
  return { interview, automation: n8n };
}

async function reschedule(id, { scheduledAt, notes }, user) {
  const existing = await getById(id);
  if (!existing) throw new AppError('Interview not found', 404);
  await assertAccess(existing, user);

  await query(
    `UPDATE interviews SET scheduled_at = ?, status = 'rescheduled', notes = COALESCE(?, notes)
     WHERE id = ?`,
    [new Date(scheduledAt), notes || null, id]
  );

  await triggerN8n({
    event: 'interview.rescheduled',
    interview_id: id,
    scheduled_at: scheduledAt,
    candidate_email: existing.email,
    job_title: existing.job_title,
  });

  await createNotification({
    userId: user.id,
    candidateId: existing.candidate_id,
    type: 'interview_rescheduled',
    title: `Interview rescheduled: ${existing.full_name}`,
    body: `New time: ${scheduledAt}`,
  });

  return getById(id);
}

async function cancel(id, user) {
  const existing = await getById(id);
  if (!existing) throw new AppError('Interview not found', 404);
  await assertAccess(existing, user);
  await query(`UPDATE interviews SET status = 'cancelled' WHERE id = ?`, [id]);
  await triggerN8n({
    event: 'interview.cancelled',
    interview_id: id,
    candidate_email: existing.email,
  });
  return getById(id);
}

async function listByJob(jobId, user) {
  const jobs = await query('SELECT id, hr_manager_id FROM jobs WHERE id = ? LIMIT 1', [
    jobId,
  ]);
  if (!jobs[0]) throw new AppError('Job not found', 404);
  if (user.role !== 'admin' && jobs[0].hr_manager_id !== user.hr_manager_id) {
    throw new AppError('Forbidden', 403);
  }
  return query(
    `SELECT i.*, c.full_name, c.email, j.title AS job_title
     FROM interviews i
     JOIN candidates c ON c.id = i.candidate_id
     JOIN jobs j ON j.id = i.job_id
     WHERE i.job_id = ?
     ORDER BY i.scheduled_at ASC`,
    [jobId]
  );
}

async function listMine(user) {
  if (user.role === 'admin') {
    return query(
      `SELECT i.*, c.full_name, c.email, j.title AS job_title
       FROM interviews i
       JOIN candidates c ON c.id = i.candidate_id
       JOIN jobs j ON j.id = i.job_id
       ORDER BY i.scheduled_at DESC
       LIMIT 100`
    );
  }
  return query(
    `SELECT i.*, c.full_name, c.email, j.title AS job_title
     FROM interviews i
     JOIN candidates c ON c.id = i.candidate_id
     JOIN jobs j ON j.id = i.job_id
     WHERE j.hr_manager_id = ?
     ORDER BY i.scheduled_at DESC
     LIMIT 100`,
    [user.hr_manager_id]
  );
}

async function getById(id) {
  const rows = await query(
    `SELECT i.*, c.full_name, c.email, j.title AS job_title, j.hr_manager_id
     FROM interviews i
     JOIN candidates c ON c.id = i.candidate_id
     JOIN jobs j ON j.id = i.job_id
     WHERE i.id = ?
     LIMIT 1`,
    [id]
  );
  return rows[0] || null;
}

async function assertAccess(interview, user) {
  if (user.role === 'admin') return;
  if (interview.hr_manager_id !== user.hr_manager_id) {
    throw new AppError('Forbidden', 403);
  }
}

async function listNotifications(userId) {
  return query(
    `SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50`,
    [userId]
  );
}

module.exports = {
  scheduleInterview,
  reschedule,
  cancel,
  listByJob,
  listMine,
  getById,
  listNotifications,
  createNotification,
};
