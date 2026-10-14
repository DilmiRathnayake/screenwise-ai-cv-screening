'use strict';

const { query } = require('../config/db');

async function getStats(hrManagerId, isAdmin) {
  const jobFilter = isAdmin ? '' : 'WHERE hr_manager_id = ?';
  const jobParams = isAdmin ? [] : [hrManagerId];

  const jobRows = await query(
    `SELECT
       COUNT(*) AS total_jobs,
       SUM(status = 'active') AS active_jobs,
       SUM(status = 'closed') AS closed_jobs,
       SUM(status = 'draft') AS draft_jobs
     FROM jobs ${jobFilter}`,
    jobParams
  );

  const candidateSql = isAdmin
    ? `SELECT
         COUNT(DISTINCT a.candidate_id) AS total_candidates,
         SUM(a.status = 'shortlisted') AS shortlisted,
         SUM(a.status = 'processed') AS processed,
         SUM(a.status = 'uploaded') AS uploaded,
         SUM(a.status = 'rejected') AS rejected
       FROM applications a`
    : `SELECT
         COUNT(DISTINCT a.candidate_id) AS total_candidates,
         SUM(a.status = 'shortlisted') AS shortlisted,
         SUM(a.status = 'processed') AS processed,
         SUM(a.status = 'uploaded') AS uploaded,
         SUM(a.status = 'rejected') AS rejected
       FROM applications a
       JOIN jobs j ON j.id = a.job_id
       WHERE j.hr_manager_id = ?`;

  const candRows = await query(candidateSql, jobParams);

  const monthlySql = isAdmin
    ? `SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, COUNT(*) AS count
       FROM applications
       WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 5 MONTH)
       GROUP BY DATE_FORMAT(created_at, '%Y-%m')
       ORDER BY month ASC`
    : `SELECT DATE_FORMAT(a.created_at, '%Y-%m') AS month, COUNT(*) AS count
       FROM applications a
       JOIN jobs j ON j.id = a.job_id
       WHERE j.hr_manager_id = ?
         AND a.created_at >= DATE_SUB(CURDATE(), INTERVAL 5 MONTH)
       GROUP BY DATE_FORMAT(a.created_at, '%Y-%m')
       ORDER BY month ASC`;

  const monthly = await query(monthlySql, jobParams);

  const jobs = jobRows[0] || {};
  const cands = candRows[0] || {};

  return {
    total_jobs: Number(jobs.total_jobs || 0),
    active_jobs: Number(jobs.active_jobs || 0),
    closed_jobs: Number(jobs.closed_jobs || 0),
    draft_jobs: Number(jobs.draft_jobs || 0),
    total_candidates: Number(cands.total_candidates || 0),
    shortlisted: Number(cands.shortlisted || 0),
    processed: Number(cands.processed || 0),
    uploaded: Number(cands.uploaded || 0),
    rejected: Number(cands.rejected || 0),
    interviews: 0,
    jobs_by_status: {
      active: Number(jobs.active_jobs || 0),
      closed: Number(jobs.closed_jobs || 0),
      draft: Number(jobs.draft_jobs || 0),
    },
    monthly_applications: monthly.map((r) => ({
      month: r.month,
      count: Number(r.count),
    })),
  };
}

module.exports = { getStats };
