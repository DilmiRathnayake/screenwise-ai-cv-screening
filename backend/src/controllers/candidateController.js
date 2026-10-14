'use strict';

const candidateService = require('../services/candidateService');
const { success } = require('../utils/response');

async function dashboard(req, res, next) {
  try {
    const data = await candidateService.getDashboard(req.user);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function applications(req, res, next) {
  try {
    const data = await candidateService.getApplications(req.user);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function interviews(req, res, next) {
  try {
    const data = await candidateService.listInterviews(req.user.email);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function profile(req, res, next) {
  try {
    const data = await candidateService.getProfile(req.user);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

module.exports = { dashboard, applications, interviews, profile };
