'use strict';

const jobRepository = require('../repositories/jobRepository');
const aiServiceClient = require('./aiServiceClient');
const { query } = require('../config/db');
const { AppError } = require('../middlewares/errorHandler');

async function resolveHrManagerId(user) {
  if (user.hr_manager_id) return user.hr_manager_id;
  if (user.role !== 'admin') return null;

  const rows = await query(
    'SELECT id FROM hr_managers ORDER BY created_at ASC LIMIT 1'
  );
  return rows[0]?.id || null;
}

async function resolveWeights(industry, rankingWeights) {
  if (rankingWeights && Object.keys(rankingWeights).length) {
    return rankingWeights;
  }
  const fromAi = await aiServiceClient.getWeights(industry || 'default');
  return fromAi.weights || {};
}

async function listJobs(user) {
  if (user.role === 'admin') {
    return jobRepository.listAll();
  }
  if (!user.hr_manager_id) {
    throw new AppError('HR profile not found', 400);
  }
  return jobRepository.listByHrManager(user.hr_manager_id);
}

async function getJob(id, user) {
  const job = await jobRepository.findById(id);
  if (!job) throw new AppError('Job not found', 404);
  assertJobAccess(job, user);
  return job;
}

async function createJob(payload, user) {
  const hrManagerId = await resolveHrManagerId(user);
  if (!hrManagerId) {
    throw new AppError(
      user.role === 'admin'
        ? 'No HR manager exists yet — register an HR account first'
        : 'HR profile required to create jobs',
      400
    );
  }

  const industry = payload.industry || 'default';
  const rankingWeights = await resolveWeights(industry, payload.rankingWeights);

  return jobRepository.create({
    hrManagerId,
    title: payload.title,
    description: payload.description,
    requiredSkills: payload.requiredSkills || [],
    minimumExperience: payload.minimumExperience ?? 0,
    educationLevel: payload.educationLevel,
    industry,
    requiredCertifications: payload.requiredCertifications || [],
    rankingWeights,
    communicationImportance: payload.communicationImportance,
    status: payload.status || 'active',
  });
}

async function updateJob(id, payload, user) {
  const existing = await getJob(id, user);
  const industry = payload.industry || existing.industry;
  const rankingWeights = await resolveWeights(
    industry,
    payload.rankingWeights || existing.ranking_weights
  );

  return jobRepository.update(id, {
    title: payload.title ?? existing.title,
    description: payload.description ?? existing.description,
    requiredSkills: payload.requiredSkills || existing.required_skills,
    minimumExperience:
      payload.minimumExperience ?? existing.minimum_experience,
    educationLevel: payload.educationLevel ?? existing.education_level,
    industry,
    requiredCertifications:
      payload.requiredCertifications || existing.required_certifications,
    rankingWeights,
    communicationImportance:
      payload.communicationImportance ?? existing.communication_importance,
    status: payload.status || existing.status,
  });
}

async function deleteJob(id, user) {
  await getJob(id, user);
  await jobRepository.remove(id);
}

async function closeJob(id, user) {
  await getJob(id, user);
  return jobRepository.setStatus(id, 'closed');
}

async function duplicateJob(id, user) {
  const job = await getJob(id, user);
  return jobRepository.create({
    hrManagerId: job.hr_manager_id,
    title: `${job.title} (Copy)`,
    description: job.description,
    requiredSkills: job.required_skills,
    minimumExperience: job.minimum_experience,
    educationLevel: job.education_level,
    industry: job.industry,
    requiredCertifications: job.required_certifications,
    rankingWeights: job.ranking_weights,
    communicationImportance: job.communication_importance,
    status: 'draft',
  });
}

function assertJobAccess(job, user) {
  if (user.role === 'admin') return;
  if (job.hr_manager_id !== user.hr_manager_id) {
    throw new AppError('Forbidden', 403);
  }
}

function toAiJobPayload(job) {
  return {
    title: job.title,
    description: job.description,
    required_skills: job.required_skills || [],
    minimum_experience: Number(job.minimum_experience || 0),
    education_level: job.education_level || null,
    industry: job.industry || 'default',
    required_certifications: job.required_certifications || [],
    ranking_weights: job.ranking_weights || null,
    communication_importance: job.communication_importance,
  };
}

module.exports = {
  listJobs,
  getJob,
  createJob,
  updateJob,
  deleteJob,
  closeJob,
  duplicateJob,
  assertJobAccess,
  toAiJobPayload,
};
