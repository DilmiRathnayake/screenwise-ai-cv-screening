'use strict';

const config = require('../config');
const applicationRepository = require('../repositories/applicationRepository');
const candidateRepository = require('../repositories/candidateRepository');
const jobService = require('./jobService');
const aiServiceClient = require('./aiServiceClient');
const { AppError } = require('../middlewares/errorHandler');

function parseJson(value, fallback) {
  if (value == null) return fallback;
  if (typeof value === 'object') return value;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function displayName(fullName, rankedName) {
  const name = (rankedName || fullName || '').trim();
  return name || 'Unnamed Candidate';
}

function criterionScoresToExplanation(criterionScores, rankingExplanation) {
  const scores = Array.isArray(criterionScores) ? criterionScores : [];
  const criteria = {};
  for (const c of scores) {
    if (c && c.criterion != null) {
      criteria[c.criterion] = Number(c.score ?? 0);
    }
  }
  const parsed = parseJson(rankingExplanation, null);
  if (parsed && typeof parsed === 'object' && parsed.criteria) {
    return parsed;
  }
  if (parsed && typeof parsed === 'object') {
    return { ...parsed, criteria: parsed.criteria || criteria };
  }
  return {
    summary: typeof rankingExplanation === 'string' ? rankingExplanation : '',
    criteria,
    strengths: [],
    gaps: [],
  };
}

function normalizeRankingRow(row, rankedFromAi) {
  const criterionScores = parseJson(row.criterion_scores, []);
  const explanationRaw = rankedFromAi?.explanation || row.ranking_explanation;
  const explanation =
    typeof explanationRaw === 'object' && explanationRaw !== null
      ? explanationRaw
      : criterionScoresToExplanation(criterionScores, explanationRaw);

  const candidateName = displayName(row.full_name, rankedFromAi?.name);

  return {
    ...row,
    candidate_name: candidateName,
    full_name: row.full_name || candidateName,
    overall_score: Number(row.matching_percentage ?? row.candidate_score ?? 0),
    score: Number(row.candidate_score ?? 0),
    explanation,
    criterion_scores: criterionScores,
  };
}

async function rankJob(jobId, user) {
  const job = await jobService.getJob(jobId, user);
  const apps = await applicationRepository.listForRanking(jobId);
  if (!apps.length) {
    throw new AppError('No candidates to rank for this job', 400);
  }

  const candidates = apps.map((row) => {
    const mapped = candidateRepository.mapCandidate({
      ...row,
      id: row.candidate_id,
      education_json: row.education_json,
      experience_json: row.experience_json,
      projects_json: row.projects_json,
      certifications_json: row.certifications_json,
      languages_json: row.languages_json,
      publications_json: row.publications_json,
      awards_json: row.awards_json,
      references_json: row.references_json,
      soft_skills_json: row.soft_skills_json,
      extraction_meta: row.extraction_meta,
      technical_skills: row.technical_skills,
    });
    return {
      candidate_id: row.application_id,
      profile: {
        name: mapped.full_name,
        email: mapped.email,
        phone: mapped.phone,
        address: mapped.address,
        linkedin: mapped.linkedin,
        github: mapped.github,
        portfolio: mapped.portfolio,
        education: mapped.education,
        experience: mapped.experience,
        technical_skills: mapped.technical_skills,
        soft_skills: mapped.soft_skills,
        languages: mapped.languages,
        projects: mapped.projects,
        publications: mapped.publications,
        certifications: mapped.certifications,
        awards: mapped.awards,
        references: mapped.references,
        years_of_experience: mapped.years_of_experience,
        communication_score: mapped.communication_score,
        raw_text: mapped.raw_text,
        extraction_meta: mapped.extraction_meta,
      },
    };
  });

  const aiResult = await aiServiceClient.rank(
    jobService.toAiJobPayload(job),
    candidates
  );

  const topCandidates = aiResult.top_candidates || [];
  const shortlistCount = Math.max(
    1,
    Math.ceil(topCandidates.length * config.shortlistTopFraction)
  );

  const saved = [];
  for (const ranked of topCandidates) {
    const applicationId = ranked.candidate_id;
    const appRow = apps.find((a) => a.application_id === applicationId);
    const candidateName = displayName(appRow?.full_name, ranked.name);

    await applicationRepository.upsertRankingResult({
      applicationId,
      jobId,
      candidateScore: ranked.candidate_score,
      matchingPercentage: ranked.matching_percentage,
      rankingPosition: ranked.ranking_position,
      semanticSimilarity: ranked.semantic_similarity,
      rankingExplanation: JSON.stringify(
        ranked.explanation || { summary: ranked.ranking_explanation }
      ),
      criterionScores: ranked.criterion_scores,
      weightsUsed: aiResult.weights_used,
    });

    const status =
      ranked.ranking_position <= shortlistCount ? 'shortlisted' : 'processed';
    await applicationRepository.updateStatus(applicationId, status);

    saved.push({
      application_id: applicationId,
      candidate_id: appRow?.candidate_id,
      name: candidateName,
      candidate_name: candidateName,
      matching_percentage: ranked.matching_percentage,
      candidate_score: ranked.candidate_score,
      overall_score: ranked.matching_percentage,
      ranking_position: ranked.ranking_position,
      ranking_explanation: ranked.ranking_explanation,
      explanation: ranked.explanation || criterionScoresToExplanation(
        ranked.criterion_scores,
        ranked.ranking_explanation
      ),
      criterion_scores: ranked.criterion_scores,
      status,
    });
  }

  return {
    job_id: jobId,
    job_title: job.title,
    industry: job.industry || 'it',
    weights_used: aiResult.weights_used,
    total_candidates: topCandidates.length,
    shortlisted: shortlistCount,
    processing_ms: aiResult.processing_ms,
    rankings: saved,
  };
}

async function getRankings(jobId, user) {
  await jobService.getJob(jobId, user);
  const rows = await applicationRepository.listRankings(jobId);
  return rows.map((r) =>
    normalizeRankingRow({
      ...r,
      criterion_scores: parseJson(r.criterion_scores, []),
      weights_used: parseJson(r.weights_used, {}),
      matching_percentage: Number(r.matching_percentage),
      candidate_score: Number(r.candidate_score),
    })
  );
}

module.exports = { rankJob, getRankings, displayName, criterionScoresToExplanation };
