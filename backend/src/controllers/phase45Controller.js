'use strict';

const searchService = require('../services/searchService');
const interviewService = require('../services/interviewService');
const { success } = require('../utils/response');

async function search(req, res, next) {
  try {
    const { query: q, topK } = req.body || {};
    const data = await searchService.semanticSearch(
      q,
      Number(topK || 10),
      req.currentUser.hr_manager_id,
      req.currentUser.role === 'admin'
    );
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function syncIndex(req, res, next) {
  try {
    const data = await searchService.syncAllCandidates();
    return success(res, data, 'Candidate index synced');
  } catch (err) {
    return next(err);
  }
}

async function schedule(req, res, next) {
  try {
    const data = await interviewService.scheduleInterview(
      req.body,
      req.currentUser
    );
    return success(res, data, 'Interview scheduled', 201);
  } catch (err) {
    return next(err);
  }
}

async function reschedule(req, res, next) {
  try {
    const data = await interviewService.reschedule(
      req.params.id,
      req.body,
      req.currentUser
    );
    return success(res, data, 'Interview rescheduled');
  } catch (err) {
    return next(err);
  }
}

async function cancel(req, res, next) {
  try {
    const data = await interviewService.cancel(req.params.id, req.currentUser);
    return success(res, data, 'Interview cancelled');
  } catch (err) {
    return next(err);
  }
}

async function listInterviews(req, res, next) {
  try {
    const data = req.params.jobId
      ? await interviewService.listByJob(req.params.jobId, req.currentUser)
      : await interviewService.listMine(req.currentUser);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function notifications(req, res, next) {
  try {
    const data = await interviewService.listNotifications(req.user.id);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

module.exports = {
  search,
  syncIndex,
  schedule,
  reschedule,
  cancel,
  listInterviews,
  notifications,
};
