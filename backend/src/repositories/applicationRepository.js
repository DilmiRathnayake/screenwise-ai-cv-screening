'use strict';

const { v4: uuidv4 } = require('uuid');
const { query } = require('../config/db');

async function createCvFile({
  candidateId,
  originalFilename,
  storedFilename,
  mimeType,
  filePath,
  fileSizeBytes,
  extractionStatus,
  extractionError,
}) {
  const id = uuidv4();
  await query(
    `INSERT INTO cv_files (
      id, candidate_id, original_filename, stored_filename, mime_type,
      file_path, file_size_bytes, extraction_status, extraction_error
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      id,
      candidateId || null,
      originalFilename,
      storedFilename,
      mimeType || null,
      filePath,
      fileSizeBytes || 0,
      extractionStatus || 'pending',
      extractionError || null,
    ]
  );
  return id;
}

async function updateCvFile(id, fields) {
  await query(
    `UPDATE cv_files SET
      candidate_id = COALESCE(?, candidate_id),
      extraction_status = COALESCE(?, extraction_status),
      extraction_error = ?
     WHERE id = ?`,
    [
      fields.candidateId ?? null,
      fields.extractionStatus ?? null,
      fields.extractionError ?? null,
      id,
    ]
  );
}

async function createApplication({ jobId, candidateId, cvFileId, status }) {
  const id = uuidv4();
  await query(
    `INSERT INTO applications (id, job_id, candidate_id, cv_file_id, status)
     VALUES (?, ?, ?, ?, ?)
     ON DUPLICATE KEY UPDATE cv_file_id = VALUES(cv_file_id), status = VALUES(status), updated_at = CURRENT_TIMESTAMP`,
    [id, jobId, candidateId, cvFileId || null, status || 'processed']
  );
  // If duplicate, fetch existing id
  const rows = await query(
    'SELECT id FROM applications WHERE job_id = ? AND candidate_id = ? LIMIT 1',
    [jobId, candidateId]
  );
  return rows[0].id;
}

async function listByJob(jobId) {
  return query(
    `SELECT a.id AS application_id, a.status AS application_status, a.created_at AS applied_at,
            c.*,
            GROUP_CONCAT(DISTINCT CASE WHEN cs.skill_type = 'technical' THEN s.name END) AS technical_skills,
            r.matching_percentage, r.candidate_score, r.ranking_position, r.ranking_explanation
     FROM applications a
     JOIN candidates c ON c.id = a.candidate_id
     LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
     LEFT JOIN skills s ON s.id = cs.skill_id
     LEFT JOIN ranking_results r ON r.application_id = a.id
     WHERE a.job_id = ?
     GROUP BY a.id, c.id, r.id
     ORDER BY COALESCE(r.ranking_position, 999999), a.created_at DESC`,
    [jobId]
  );
}

async function listForRanking(jobId) {
  return query(
    `SELECT a.id AS application_id, a.candidate_id, a.status,
            c.full_name, c.email, c.phone, c.address, c.linkedin, c.github, c.portfolio,
            c.years_of_experience, c.communication_score, c.education_json, c.experience_json,
            c.projects_json, c.certifications_json, c.languages_json, c.publications_json,
            c.awards_json, c.references_json, c.soft_skills_json, c.raw_text, c.extraction_meta,
            GROUP_CONCAT(DISTINCT CASE WHEN cs.skill_type = 'technical' THEN s.name END) AS technical_skills
     FROM applications a
     JOIN candidates c ON c.id = a.candidate_id
     LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id AND cs.skill_type = 'technical'
     LEFT JOIN skills s ON s.id = cs.skill_id
     WHERE a.job_id = ? AND a.status IN ('uploaded', 'processed', 'shortlisted', 'rejected')
     GROUP BY a.id, c.id`,
    [jobId]
  );
}

async function updateStatus(applicationId, status) {
  await query('UPDATE applications SET status = ? WHERE id = ?', [
    status,
    applicationId,
  ]);
}

async function upsertRankingResult(row) {
  const existing = await query(
    'SELECT id FROM ranking_results WHERE application_id = ? LIMIT 1',
    [row.applicationId]
  );
  if (existing[0]) {
    await query(
      `UPDATE ranking_results SET
        candidate_score = ?, matching_percentage = ?, ranking_position = ?,
        semantic_similarity = ?, ranking_explanation = ?, criterion_scores = ?,
        weights_used = ?
       WHERE application_id = ?`,
      [
        row.candidateScore,
        row.matchingPercentage,
        row.rankingPosition,
        row.semanticSimilarity ?? null,
        row.rankingExplanation || null,
        JSON.stringify(row.criterionScores || []),
        JSON.stringify(row.weightsUsed || {}),
        row.applicationId,
      ]
    );
    return existing[0].id;
  }
  const id = uuidv4();
  await query(
    `INSERT INTO ranking_results (
      id, application_id, job_id, candidate_score, matching_percentage,
      ranking_position, semantic_similarity, ranking_explanation,
      criterion_scores, weights_used
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      id,
      row.applicationId,
      row.jobId,
      row.candidateScore,
      row.matchingPercentage,
      row.rankingPosition,
      row.semanticSimilarity ?? null,
      row.rankingExplanation || null,
      JSON.stringify(row.criterionScores || []),
      JSON.stringify(row.weightsUsed || {}),
    ]
  );
  return id;
}

async function listByCandidateEmail(email) {
  return query(
    `SELECT a.id AS application_id, a.status AS application_status, a.created_at AS applied_at,
            c.id AS candidate_id, c.full_name, c.email,
            j.id AS job_id, j.title AS job_title, j.industry,
            hm.company AS company_name,
            r.matching_percentage, r.candidate_score, r.ranking_position, r.ranking_explanation,
            r.criterion_scores,
            (SELECT COUNT(*) FROM interviews i
             WHERE i.application_id = a.id AND i.status IN ('scheduled', 'rescheduled')) AS interview_count
     FROM applications a
     JOIN candidates c ON c.id = a.candidate_id
     JOIN jobs j ON j.id = a.job_id
     JOIN hr_managers hm ON hm.id = j.hr_manager_id
     LEFT JOIN ranking_results r ON r.application_id = a.id
     WHERE LOWER(c.email) = LOWER(?)
     ORDER BY a.created_at DESC`,
    [email]
  );
}

async function listAppliedJobIdsForEmail(email) {
  const rows = await query(
    `SELECT DISTINCT a.job_id
     FROM applications a
     JOIN candidates c ON c.id = a.candidate_id
     WHERE LOWER(c.email) = LOWER(?)`,
    [email]
  );
  return rows.map((r) => r.job_id);
}

async function listRankings(jobId) {
  return query(
    `SELECT r.*, a.candidate_id, c.full_name, c.email
     FROM ranking_results r
     JOIN applications a ON a.id = r.application_id
     JOIN candidates c ON c.id = a.candidate_id
     WHERE r.job_id = ?
     ORDER BY r.ranking_position ASC`,
    [jobId]
  );
}

module.exports = {
  createCvFile,
  updateCvFile,
  createApplication,
  listByJob,
  listByCandidateEmail,
  listAppliedJobIdsForEmail,
  listForRanking,
  updateStatus,
  upsertRankingResult,
  listRankings,
};
