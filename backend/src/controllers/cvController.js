'use strict';

const cvService = require('../services/cvService');
const rankingService = require('../services/rankingService');
const { success } = require('../utils/response');

async function uploadSingle(req, res, next) {
  try {
    const data = await cvService.uploadSingle(
      req.params.jobId,
      req.file,
      req.currentUser
    );
    return success(res, data, 'CV processed', 201);
  } catch (err) {
    return next(err);
  }
}

async function uploadBulk(req, res, next) {
  try {
    const data = await cvService.uploadBulk(
      req.params.jobId,
      req.files,
      req.currentUser
    );
    return success(res, data, 'Bulk CV processing complete', 201);
  } catch (err) {
    return next(err);
  }
}

async function listCandidates(req, res, next) {
  try {
    const data = await cvService.listJobCandidates(
      req.params.jobId,
      req.currentUser
    );
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function getCandidate(req, res, next) {
  try {
    const data = await cvService.getCandidate(req.params.id);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function rank(req, res, next) {
  try {
    const data = await rankingService.rankJob(
      req.params.jobId,
      req.currentUser
    );
    return success(res, data, 'Candidates ranked');
  } catch (err) {
    return next(err);
  }
}

async function rankings(req, res, next) {
  try {
    const data = await rankingService.getRankings(
      req.params.jobId,
      req.currentUser
    );
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

module.exports = {
  uploadSingle,
  uploadBulk,
  listCandidates,
  getCandidate,
  rank,
  rankings,
};
