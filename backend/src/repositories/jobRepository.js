'use strict';

const { v4: uuidv4 } = require('uuid');
const { query, withTransaction } = require('../config/db');

function parseJson(value, fallback) {
  if (value == null) return fallback;
  if (typeof value === 'object') return value;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function mapJob(row) {
  if (!row) return null;
  return {
    ...row,
    required_certifications: parseJson(row.required_certifications, []),
    ranking_weights: parseJson(row.ranking_weights, {}),
    required_skills: row.required_skills
      ? String(row.required_skills).split(',').filter(Boolean)
      : [],
    minimum_experience: Number(row.minimum_experience),
    communication_importance:
      row.communication_importance != null
        ? Number(row.communication_importance)
        : null,
  };
}

async function findSkillsByJobId(jobId) {
  const rows = await query(
    `SELECT s.name FROM job_skills js
     JOIN skills s ON s.id = js.skill_id
     WHERE js.job_id = ?
     ORDER BY s.name`,
    [jobId]
  );
  return rows.map((r) => r.name);
}

async function ensureSkill(connection, name) {
  const normalized = String(name).trim().toLowerCase();
  if (!normalized) return null;

  const [existing] = await connection.execute(
    'SELECT id FROM skills WHERE normalized = ? LIMIT 1',
    [normalized]
  );
  if (existing[0]) return existing[0].id;

  try {
    const [result] = await connection.execute(
      'INSERT INTO skills (name, normalized) VALUES (?, ?)',
      [String(name).trim(), normalized]
    );
    return result.insertId;
  } catch (err) {
    if (err.code === 'ER_DUP_ENTRY') {
      const [again] = await connection.execute(
        'SELECT id FROM skills WHERE normalized = ? LIMIT 1',
        [normalized]
      );
      return again[0]?.id || null;
    }
    throw err;
  }
}

async function linkJobSkills(connection, jobId, skillNames = []) {
  await connection.execute('DELETE FROM job_skills WHERE job_id = ?', [jobId]);
  for (const name of skillNames) {
    const skillId = await ensureSkill(connection, name);
    if (!skillId) continue;
    await connection.execute(
      'INSERT IGNORE INTO job_skills (job_id, skill_id) VALUES (?, ?)',
      [jobId, skillId]
    );
  }
}

async function listByHrManager(hrManagerId) {
  const rows = await query(
    `SELECT j.*,
            GROUP_CONCAT(s.name ORDER BY s.name SEPARATOR ',') AS required_skills
     FROM jobs j
     LEFT JOIN job_skills js ON js.job_id = j.id
     LEFT JOIN skills s ON s.id = js.skill_id
     WHERE j.hr_manager_id = ?
     GROUP BY j.id
     ORDER BY j.created_at DESC`,
    [hrManagerId]
  );
  return rows.map(mapJob);
}

async function listAll() {
  const rows = await query(
    `SELECT j.*,
            GROUP_CONCAT(s.name ORDER BY s.name SEPARATOR ',') AS required_skills
     FROM jobs j
     LEFT JOIN job_skills js ON js.job_id = j.id
     LEFT JOIN skills s ON s.id = js.skill_id
     GROUP BY j.id
     ORDER BY j.created_at DESC`
  );
  return rows.map(mapJob);
}

async function findById(id) {
  const rows = await query(
    `SELECT j.*,
            GROUP_CONCAT(s.name ORDER BY s.name SEPARATOR ',') AS required_skills
     FROM jobs j
     LEFT JOIN job_skills js ON js.job_id = j.id
     LEFT JOIN skills s ON s.id = js.skill_id
     WHERE j.id = ?
     GROUP BY j.id
     LIMIT 1`,
    [id]
  );
  return mapJob(rows[0]);
}

async function create(job) {
  const id = uuidv4();
  await withTransaction(async (conn) => {
    await conn.execute(
      `INSERT INTO jobs (
        id, hr_manager_id, title, description, minimum_experience,
        education_level, industry, required_certifications, ranking_weights,
        communication_importance, status
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        id,
        job.hrManagerId,
        job.title,
        job.description,
        job.minimumExperience ?? 0,
        job.educationLevel || null,
        job.industry || 'default',
        JSON.stringify(job.requiredCertifications || []),
        JSON.stringify(job.rankingWeights || {}),
        job.communicationImportance ?? null,
        job.status || 'active',
      ]
    );
    await linkJobSkills(conn, id, job.requiredSkills || []);
  });
  return findById(id);
}

async function update(id, job) {
  await withTransaction(async (conn) => {
    await conn.execute(
      `UPDATE jobs SET
        title = ?, description = ?, minimum_experience = ?,
        education_level = ?, industry = ?, required_certifications = ?,
        ranking_weights = ?, communication_importance = ?, status = ?
       WHERE id = ?`,
      [
        job.title,
        job.description,
        job.minimumExperience ?? 0,
        job.educationLevel || null,
        job.industry || 'default',
        JSON.stringify(job.requiredCertifications || []),
        JSON.stringify(job.rankingWeights || {}),
        job.communicationImportance ?? null,
        job.status || 'active',
        id,
      ]
    );
    if (job.requiredSkills) {
      await linkJobSkills(conn, id, job.requiredSkills);
    }
  });
  return findById(id);
}

async function remove(id) {
  await query('DELETE FROM jobs WHERE id = ?', [id]);
}

async function setStatus(id, status) {
  await query('UPDATE jobs SET status = ? WHERE id = ?', [status, id]);
  return findById(id);
}

module.exports = {
  listByHrManager,
  listAll,
  findById,
  create,
  update,
  remove,
  setStatus,
  findSkillsByJobId,
  ensureSkill,
};
