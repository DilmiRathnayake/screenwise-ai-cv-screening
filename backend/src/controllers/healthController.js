'use strict';

const db = require('../config/db');
const aiServiceClient = require('../services/aiServiceClient');
const { success } = require('../utils/response');
const config = require('../config');

async function health(req, res) {
  let database = { ok: false };
  let ai = { ok: false };

  try {
    database = { ok: await db.ping() };
  } catch (err) {
    database = { ok: false, error: err.message };
  }

  try {
    const aiHealth = await aiServiceClient.health();
    ai = { ok: true, ...aiHealth };
  } catch (err) {
    ai = { ok: false, error: err.message };
  }

  const ok = database.ok;
  return res.status(ok ? 200 : 503).json({
    success: ok,
    message: ok ? 'Backend healthy' : 'Backend degraded',
    data: {
      service: 'cv-screening-backend',
      version: '1.0.0',
      env: config.nodeEnv,
      database,
      ai,
    },
  });
}

async function industries(req, res, next) {
  try {
    const data = await aiServiceClient.listIndustries();
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function weights(req, res, next) {
  try {
    const data = await aiServiceClient.getWeights(req.params.industry);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

async function model2Metrics(req, res, next) {
  try {
    const data = await aiServiceClient.getModel2Metrics();
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

module.exports = { health, industries, weights, model2Metrics };
