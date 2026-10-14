'use strict';

const jobService = require('../services/jobService');
const { success } = require('../utils/response');

async function list(req, res, next) {
  try {
    const data = await jobService.listJobs(req.currentUser);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function getById(req, res, next) {
  try {
    const data = await jobService.getJob(req.params.id, req.currentUser);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function create(req, res, next) {
  try {
    const data = await jobService.createJob(req.body, req.currentUser);
    return success(res, data, 'Job created', 201);
  } catch (err) {
    return next(err);
  }
}

async function update(req, res, next) {
  try {
    const data = await jobService.updateJob(
      req.params.id,
      req.body,
      req.currentUser
    );
    return success(res, data, 'Job updated');
  } catch (err) {
    return next(err);
  }
}

async function remove(req, res, next) {
  try {
    await jobService.deleteJob(req.params.id, req.currentUser);
    return success(res, null, 'Job deleted');
  } catch (err) {
    return next(err);
  }
}

async function close(req, res, next) {
  try {
    const data = await jobService.closeJob(req.params.id, req.currentUser);
    return success(res, data, 'Job closed');
  } catch (err) {
    return next(err);
  }
}

async function duplicate(req, res, next) {
  try {
    const data = await jobService.duplicateJob(req.params.id, req.currentUser);
    return success(res, data, 'Job duplicated', 201);
  } catch (err) {
    return next(err);
  }
}

module.exports = { list, getById, create, update, remove, close, duplicate };
