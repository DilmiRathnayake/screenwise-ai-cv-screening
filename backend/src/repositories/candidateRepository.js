'use strict';

const { v4: uuidv4 } = require('uuid');
const { query, withTransaction } = require('../config/db');
const { ensureSkill } = require('./jobRepository');

function parseJson(value, fallback) {
  if (value == null) return fallback;
  if (typeof value === 'object') return value;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function mapCandidate(row) {
  if (!row) return null;
  return {
    id: row.id,
    full_name: row.full_name,
    email: row.email,
    phone: row.phone,
    address: row.address,
    linkedin: row.linkedin,
    github: row.github,
    portfolio: row.portfolio,
    years_of_experience:
      row.years_of_experience != null ? Number(row.years_of_experience) : null,
    communication_score: Number(row.communication_score ?? 0.5),
    education: parseJson(row.education_json, []),
    experience: parseJson(row.experience_json, []),
    projects: parseJson(row.projects_json, []),
    certifications: parseJson(row.certifications_json, []),
    languages: parseJson(row.languages_json, []),
    publications: parseJson(row.publications_json, []),
    awards: parseJson(row.awards_json, []),
    references: parseJson(row.references_json, []),
    soft_skills: parseJson(row.soft_skills_json, []),
    technical_skills: row.technical_skills
      ? String(row.technical_skills).split(',').filter(Boolean)
      : [],
    raw_text: row.raw_text,
    extraction_meta: parseJson(row.extraction_meta, {}),
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

async function findPrimaryByEmail(email) {
  if (!email) return null;
  const rows = await query(
    `SELECT c.*,
            GROUP_CONCAT(DISTINCT CASE WHEN cs.skill_type = 'technical' THEN s.name END) AS technical_skills
     FROM candidates c
     LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
     LEFT JOIN skills s ON s.id = cs.skill_id
     WHERE LOWER(c.email) = LOWER(?)
     GROUP BY c.id
     ORDER BY c.updated_at DESC
     LIMIT 1`,
    [email]
  );
  return mapCandidate(rows[0]);
}

async function ensureStubForUser({ email, fullName }) {
  const existing = await findPrimaryByEmail(email);
  if (existing) return existing;
  return createFromProfile({
    name: fullName || email.split('@')[0],
    email,
    technical_skills: [],
    education: [],
    experience: [],
    projects: [],
    certifications: [],
    communication_score: 0.5,
    raw_text: '',
    extraction_meta: { source: 'candidate_registration' },
  });
}

async function findById(id) {
  const rows = await query(
    `SELECT c.*,
            GROUP_CONCAT(DISTINCT CASE WHEN cs.skill_type = 'technical' THEN s.name END) AS technical_skills
     FROM candidates c
     LEFT JOIN candidate_skills cs ON cs.candidate_id = c.id
     LEFT JOIN skills s ON s.id = cs.skill_id
     WHERE c.id = ?
     GROUP BY c.id
     LIMIT 1`,
    [id]
  );
  return mapCandidate(rows[0]);
}

async function createFromProfile(profile) {
  const id = uuidv4();
  await withTransaction(async (conn) => {
    await conn.execute(
      `INSERT INTO candidates (
        id, full_name, email, phone, address, linkedin, github, portfolio,
        years_of_experience, communication_score, education_json, experience_json,
        projects_json, certifications_json, languages_json, publications_json,
        awards_json, references_json, soft_skills_json, raw_text, extraction_meta
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        id,
        profile.name || null,
        profile.email || null,
        profile.phone || null,
        profile.address || null,
        profile.linkedin || null,
        profile.github || null,
        profile.portfolio || null,
        profile.years_of_experience ?? null,
        profile.communication_score ?? 0.5,
        JSON.stringify(profile.education || []),
        JSON.stringify(profile.experience || []),
        JSON.stringify(profile.projects || []),
        JSON.stringify(profile.certifications || []),
        JSON.stringify(profile.languages || []),
        JSON.stringify(profile.publications || []),
        JSON.stringify(profile.awards || []),
        JSON.stringify(profile.references || []),
        JSON.stringify(profile.soft_skills || []),
        profile.raw_text || null,
        JSON.stringify(profile.extraction_meta || {}),
      ]
    );

    for (const skill of profile.technical_skills || []) {
      const skillId = await ensureSkill(conn, skill);
      if (skillId) {
        await conn.execute(
          'INSERT IGNORE INTO candidate_skills (candidate_id, skill_id, skill_type) VALUES (?, ?, ?)',
          [id, skillId, 'technical']
        );
      }
    }
    for (const skill of profile.soft_skills || []) {
      const skillId = await ensureSkill(conn, skill);
      if (skillId) {
        await conn.execute(
          'INSERT IGNORE INTO candidate_skills (candidate_id, skill_id, skill_type) VALUES (?, ?, ?)',
          [id, skillId, 'soft']
        );
      }
    }
  });
  return findById(id);
}

async function toAiProfile(candidate) {
  return {
    name: candidate.full_name,
    email: candidate.email,
    phone: candidate.phone,
    address: candidate.address,
    linkedin: candidate.linkedin,
    github: candidate.github,
    portfolio: candidate.portfolio,
    education: candidate.education || [],
    experience: candidate.experience || [],
    technical_skills: candidate.technical_skills || [],
    soft_skills: candidate.soft_skills || [],
    languages: candidate.languages || [],
    projects: candidate.projects || [],
    publications: candidate.publications || [],
    certifications: candidate.certifications || [],
    awards: candidate.awards || [],
    references: candidate.references || [],
    years_of_experience: candidate.years_of_experience,
    communication_score: candidate.communication_score,
    raw_text: candidate.raw_text,
    extraction_meta: candidate.extraction_meta || {},
  };
}

module.exports = {
  findById,
  findPrimaryByEmail,
  ensureStubForUser,
  createFromProfile,
  toAiProfile,
  mapCandidate,
};
