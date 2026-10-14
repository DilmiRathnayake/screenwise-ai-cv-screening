'use strict';

const fs = require('fs');
const candidateRepository = require('../repositories/candidateRepository');
const applicationRepository = require('../repositories/applicationRepository');
const jobService = require('./jobService');
const aiServiceClient = require('./aiServiceClient');
const { AppError } = require('../middlewares/errorHandler');
const logger = require('../utils/logger');

async function processUploadedFile(jobId, file, user) {
  const job = await jobService.getJob(jobId, user);
  const buffer = fs.readFileSync(file.path);

  let extractResult;
  try {
    extractResult = await aiServiceClient.extract(buffer, file.originalname);
  } catch (err) {
    const cvId = await applicationRepository.createCvFile({
      candidateId: null,
      originalFilename: file.originalname,
      storedFilename: file.filename,
      mimeType: file.mimetype,
      filePath: file.path,
      fileSizeBytes: file.size,
      extractionStatus: 'failed',
      extractionError: err.message,
    });
    throw new AppError(
      `Extraction failed for ${file.originalname}: ${err.message}`,
      502,
      { cvFileId: cvId }
    );
  }

  const profile = extractResult.profile;
  const candidate = await candidateRepository.createFromProfile(profile);

  const cvFileId = await applicationRepository.createCvFile({
    candidateId: candidate.id,
    originalFilename: file.originalname,
    storedFilename: file.filename,
    mimeType: file.mimetype,
    filePath: file.path,
    fileSizeBytes: file.size,
    extractionStatus: 'success',
    extractionError: null,
  });

  const applicationId = await applicationRepository.createApplication({
    jobId: job.id,
    candidateId: candidate.id,
    cvFileId,
    status: 'processed',
  });

  // Phase 4: index candidate for semantic search (best-effort)
  try {
    const searchService = require('./searchService');
    await searchService.indexCandidate(candidate.id, { job_id: job.id });
  } catch (err) {
    logger.warn(`Post-upload indexing skipped: ${err.message}`);
  }

  return {
    applicationId,
    cvFileId,
    candidate,
    processingMs: extractResult.processing_ms,
    filename: file.originalname,
  };
}

async function uploadSingle(jobId, file, user) {
  if (!file) throw new AppError('CV file is required', 400);
  return processUploadedFile(jobId, file, user);
}

async function uploadBulk(jobId, files, user) {
  if (!files || !files.length) throw new AppError('At least one CV file is required', 400);
  await jobService.getJob(jobId, user);

  const results = [];
  for (const file of files) {
    try {
      const item = await processUploadedFile(jobId, file, user);
      results.push({ success: true, ...item });
    } catch (err) {
      logger.error(`Bulk upload item failed: ${err.message}`);
      results.push({
        success: false,
        filename: file.originalname,
        error: err.message,
      });
    }
  }
  return {
    total: results.length,
    succeeded: results.filter((r) => r.success).length,
    failed: results.filter((r) => !r.success).length,
    results,
  };
}

async function listJobCandidates(jobId, user) {
  await jobService.getJob(jobId, user);
  const rows = await applicationRepository.listByJob(jobId);
  return rows.map((row) => {
    const mapped = candidateRepository.mapCandidate(row);
    const fullName = (mapped.full_name || '').trim();
    const candidateName = fullName || 'Unnamed Candidate';
    return {
      application_id: row.application_id,
      candidate_id: row.candidate_id,
      application_status: row.application_status,
      applied_at: row.applied_at,
      matching_percentage: row.matching_percentage,
      candidate_score: row.candidate_score,
      ranking_position: row.ranking_position,
      ranking_explanation: row.ranking_explanation,
      full_name: fullName || null,
      candidate_name: candidateName,
      email: mapped.email,
      candidate: mapped,
    };
  });
}

async function getCandidate(id) {
  const candidate = await candidateRepository.findById(id);
  if (!candidate) throw new AppError('Candidate not found', 404);
  return candidate;
}

module.exports = {
  uploadSingle,
  uploadBulk,
  listJobCandidates,
  getCandidate,
};
