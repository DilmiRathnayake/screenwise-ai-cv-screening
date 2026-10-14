'use strict';

const { query } = require('../config/db');
const candidateRepository = require('../repositories/candidateRepository');
const applicationRepository = require('../repositories/applicationRepository');
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

function computeCompletion(candidate) {
  if (!candidate) return 10;
  const checks = [
    candidate.full_name,
    candidate.email,
    candidate.phone,
    candidate.years_of_experience != null,
    (candidate.technical_skills?.length || 0) > 0,
    (candidate.education?.length || 0) > 0,
    (candidate.projects?.length || 0) > 0,
    candidate.raw_text,
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

function deriveTitle(candidate) {
  const exp = candidate?.experience || [];
  if (exp.length && exp[0]?.title) return exp[0].title;
  if (exp.length && exp[0]?.role) return exp[0].role;
  return 'IT Professional';
}

function deriveLocation(candidate) {
  return (candidate?.address || '').trim() || '—';
}

function statusLabel(row) {
  if (Number(row.interview_count) > 0) return 'Interview';
  const map = {
    uploaded: 'Applied',
    processed: 'Screening',
    shortlisted: 'Shortlisted',
    rejected: 'Rejected',
  };
  return map[row.application_status] || row.application_status;
}

function statusProgress(row) {
  if (Number(row.interview_count) > 0) return 85;
  const map = { uploaded: 20, processed: 40, shortlisted: 70, rejected: 100 };
  return map[row.application_status] || 25;
}

function mapApplicationRow(row) {
  return {
    id: row.application_id,
    role: row.job_title,
    company: row.company_name,
    status: statusLabel(row),
    progress: statusProgress(row),
    matching_percentage: row.matching_percentage != null ? Number(row.matching_percentage) : null,
    applied_at: row.applied_at,
    job_id: row.job_id,
  };
}

function collectFeedback(applications) {
  const lines = [];
  const seen = new Set();
  for (const row of applications) {
    const explanation = parseJson(row.ranking_explanation, null);
    const gaps = explanation?.gaps || [];
    const strengths = explanation?.strengths || [];
    for (const item of [...strengths, ...gaps]) {
      const text = String(item).trim();
      if (text && !seen.has(text.toLowerCase())) {
        seen.add(text.toLowerCase());
        lines.push(text);
      }
    }
    if (explanation?.summary && !seen.has(explanation.summary.toLowerCase())) {
      seen.add(explanation.summary.toLowerCase());
      lines.push(explanation.summary);
    }
  }
  if (!lines.length) {
    return [
      'Upload or apply to roles to receive AI ranking feedback.',
      'Complete your profile to improve match visibility.',
    ];
  }
  return lines.slice(0, 6);
}

function buildAchievements(profile, applications, interviews) {
  const achievements = [];
  if (profile.completion >= 80) achievements.push('Profile 80%+');
  if (interviews.length) achievements.push('First interview booked');
  if (profile.resumeScore >= 85) achievements.push('Resume AI score 85+');
  if (applications.length) achievements.push(`${applications.length} application${applications.length > 1 ? 's' : ''} tracked`);
  return achievements;
}

function buildProfile(user, candidate, applications) {
  const completion = computeCompletion(candidate);
  const rankedScores = applications
    .map((a) => a.matching_percentage)
    .filter((v) => v != null && !Number.isNaN(Number(v)));
  const resumeScore = rankedScores.length
    ? Math.round(Math.max(...rankedScores.map(Number)))
    : Math.round(Number(candidate?.communication_score ?? 0.5) * 100);

  return {
    name: candidate?.full_name || user.email.split('@')[0],
    title: deriveTitle(candidate),
    email: user.email,
    completion,
    resumeScore,
    location: deriveLocation(candidate),
    candidate_id: candidate?.id || null,
  };
}

function simpleMatchScore(job, candidate) {
  const required = (job.required_skills || []).map((s) => String(s).toLowerCase());
  const skills = (candidate.technical_skills || []).map((s) => String(s).toLowerCase());
  if (!required.length) return 55;
  const skillSet = new Set(skills);
  const hits = required.filter((s) => skillSet.has(s)).length;
  const expBonus =
    candidate.years_of_experience != null &&
    Number(candidate.years_of_experience) >= Number(job.minimum_experience || 0)
      ? 10
      : 0;
  return Math.min(99, Math.round((hits / required.length) * 90 + expBonus));
}

async function rankRecommendations(candidate, jobs) {
  const profile = await candidateRepository.toAiProfile(candidate);
  const ranked = [];

  for (const job of jobs.slice(0, 8)) {
    try {
      const aiResult = await aiServiceClient.rank(jobService.toAiJobPayload(job), [
        {
          candidate_id: 'preview',
          profile: {
            name: profile.name,
            email: profile.email,
            phone: profile.phone,
            address: profile.address,
            education: profile.education,
            experience: profile.experience,
            technical_skills: profile.technical_skills,
            soft_skills: profile.soft_skills,
            projects: profile.projects,
            certifications: profile.certifications,
            years_of_experience: profile.years_of_experience,
            communication_score: profile.communication_score,
            raw_text: profile.raw_text,
          },
        },
      ]);
      const top = aiResult.top_candidates?.[0];
      ranked.push({
        id: job.id,
        title: job.title,
        company: job.company_name || 'Employer',
        match: Math.round(Number(top?.matching_percentage ?? simpleMatchScore(job, candidate))),
      });
    } catch {
      ranked.push({
        id: job.id,
        title: job.title,
        company: job.company_name || 'Employer',
        match: simpleMatchScore(job, candidate),
      });
    }
  }

  return ranked.sort((a, b) => b.match - a.match).slice(0, 3);
}

async function listRecommendedJobs(email, candidate) {
  const appliedIds = await applicationRepository.listAppliedJobIdsForEmail(email);
  const rows = await query(
    `SELECT j.*,
            GROUP_CONCAT(s.name ORDER BY s.name SEPARATOR ',') AS required_skills,
            hm.company AS company_name
     FROM jobs j
     LEFT JOIN job_skills js ON js.job_id = j.id
     LEFT JOIN skills s ON s.id = js.skill_id
     JOIN hr_managers hm ON hm.id = j.hr_manager_id
     WHERE j.status = 'active'
     ${appliedIds.length ? `AND j.id NOT IN (${appliedIds.map(() => '?').join(',')})` : ''}
     GROUP BY j.id
     ORDER BY j.created_at DESC
     LIMIT 12`,
    appliedIds
  );
  const jobs = rows.map((row) => ({
    id: row.id,
    title: row.title,
    description: row.description,
    minimum_experience: Number(row.minimum_experience || 0),
    education_level: row.education_level,
    industry: row.industry || 'default',
    required_certifications: parseJson(row.required_certifications, []),
    ranking_weights: parseJson(row.ranking_weights, {}),
    required_skills: row.required_skills
      ? String(row.required_skills).split(',').filter(Boolean)
      : [],
    communication_importance:
      row.communication_importance != null ? Number(row.communication_importance) : null,
    company_name: row.company_name,
  }));
  if (!jobs.length) return [];
  return rankRecommendations(candidate, jobs);
}

async function listInterviews(email) {
  const rows = await query(
    `SELECT i.*, c.full_name, c.email, j.title AS job_title, hm.company AS company_name
     FROM interviews i
     JOIN candidates c ON c.id = i.candidate_id
     JOIN jobs j ON j.id = i.job_id
     JOIN hr_managers hm ON hm.id = j.hr_manager_id
     WHERE LOWER(c.email) = LOWER(?)
       AND i.status IN ('scheduled', 'rescheduled', 'completed')
     ORDER BY i.scheduled_at ASC`,
    [email]
  );
  return rows.map((i) => ({
    id: i.id,
    title: `${i.company_name || 'Company'} · ${i.job_title}`,
    start: i.scheduled_at,
    status: i.status,
    mode: i.mode,
    meeting_link: i.meeting_link,
    location: i.location,
    job_title: i.job_title,
    company: i.company_name,
  }));
}

async function assertCandidateUser(user) {
  if (!user || user.role !== 'candidate') {
    throw new AppError('Candidate access required', 403);
  }
}

async function getDashboard(user) {
  await assertCandidateUser(user);
  const candidate =
    (await candidateRepository.findPrimaryByEmail(user.email)) ||
    (await candidateRepository.ensureStubForUser({
      email: user.email,
      fullName: user.full_name,
    }));

  const rawApps = await applicationRepository.listByCandidateEmail(user.email);
  const applications = rawApps.map(mapApplicationRow);
  const profile = buildProfile(user, candidate, rawApps);
  const interviews = await listInterviews(user.email);
  const recommended = await listRecommendedJobs(user.email, candidate);
  const feedback = collectFeedback(rawApps);
  const achievements = buildAchievements(profile, applications, interviews);

  return { profile, applications, recommended, feedback, achievements, interviews };
}

async function getApplications(user) {
  await assertCandidateUser(user);
  const rows = await applicationRepository.listByCandidateEmail(user.email);
  return rows.map(mapApplicationRow);
}

async function getProfile(user) {
  await assertCandidateUser(user);
  const candidate =
    (await candidateRepository.findPrimaryByEmail(user.email)) ||
    (await candidateRepository.ensureStubForUser({
      email: user.email,
      fullName: user.full_name,
    }));
  const rawApps = await applicationRepository.listByCandidateEmail(user.email);
  return {
    profile: buildProfile(user, candidate, rawApps),
    candidate,
  };
}

module.exports = {
  getDashboard,
  getApplications,
  getProfile,
  listInterviews,
};
