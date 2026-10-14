'use strict';

const { query } = require('../config/db');
const candidateRepository = require('../repositories/candidateRepository');
const aiServiceClient = require('./aiServiceClient');
const logger = require('../utils/logger');
const { AppError } = require('../middlewares/errorHandler');

function profileToText(candidate) {
  const parts = [
    candidate.full_name,
    candidate.email,
    (candidate.technical_skills || []).join(' '),
    (candidate.soft_skills || []).join(' '),
    (candidate.education || [])
      .map((e) => [e.degree, e.university, e.field].filter(Boolean).join(' '))
      .join(' '),
    (candidate.experience || [])
      .map((e) => [e.job_title, e.company, e.description].filter(Boolean).join(' '))
      .join(' '),
    (candidate.projects || [])
      .map((p) => [p.name, p.description, (p.technologies || []).join(' ')].filter(Boolean).join(' '))
      .join(' '),
    (candidate.certifications || []).join(' '),
    candidate.raw_text,
  ];
  return parts.filter(Boolean).join('\n').slice(0, 12000);
}

async function indexCandidate(candidateId, extraMeta = {}) {
  const candidate = await candidateRepository.findById(candidateId);
  if (!candidate) return null;

  const text = profileToText(candidate);
  try {
    await aiServiceClient.upsertEmbeddings([
      {
        id: candidateId,
        text: text || candidate.full_name || 'candidate',
        metadata: {
          candidate_id: candidateId,
          name: candidate.full_name || '',
          email: candidate.email || '',
          years_of_experience: candidate.years_of_experience ?? '',
          ...extraMeta,
        },
      },
    ]);
    return true;
  } catch (err) {
    logger.warn(`Vector index failed for ${candidateId}: ${err.message}`);
    return false;
  }
}

async function syncAllCandidates() {
  const rows = await query('SELECT id FROM candidates ORDER BY created_at DESC LIMIT 500');
  let ok = 0;
  for (const row of rows) {
    const indexed = await indexCandidate(row.id);
    if (indexed) ok += 1;
  }
  return { total: rows.length, indexed: ok };
}

async function semanticSearch(queryText, topK = 10, hrManagerId, isAdmin) {
  if (!queryText || queryText.trim().length < 2) {
    throw new AppError('Search query is required', 400);
  }

  const aiResult = await aiServiceClient.semanticSearch(queryText, topK);
  const hits = aiResult.results || [];

  // Enrich with DB candidate + restrict to HR's applicants when not admin
  const enriched = [];
  for (const hit of hits) {
    const candidateId = hit.metadata?.candidate_id || hit.id;
    const candidate = await candidateRepository.findById(candidateId);
    if (!candidate) continue;

    if (!isAdmin && hrManagerId) {
      const apps = await query(
        `SELECT a.id, a.job_id, a.status, j.title AS job_title
         FROM applications a
         JOIN jobs j ON j.id = a.job_id
         WHERE a.candidate_id = ? AND j.hr_manager_id = ?
         LIMIT 5`,
        [candidateId, hrManagerId]
      );
      if (!apps.length) continue;
      enriched.push({
        score: hit.score,
        text_preview: hit.text_preview,
        candidate,
        applications: apps,
      });
    } else {
      enriched.push({
        score: hit.score,
        text_preview: hit.text_preview,
        candidate,
        applications: [],
      });
    }
  }

  return {
    query: queryText,
    backend: aiResult.backend,
    processing_ms: aiResult.processing_ms,
    total: enriched.length,
    results: enriched,
  };
}

module.exports = {
  indexCandidate,
  syncAllCandidates,
  semanticSearch,
  profileToText,
};
