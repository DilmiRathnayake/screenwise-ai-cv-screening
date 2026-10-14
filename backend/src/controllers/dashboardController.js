'use strict';

const dashboardService = require('../services/dashboardService');
const { success } = require('../utils/response');
const { AppError } = require('../middlewares/errorHandler');

async function stats(req, res, next) {
  try {
    const isAdmin = req.currentUser.role === 'admin';
    if (!isAdmin && !req.currentUser.hr_manager_id) {
      throw new AppError('HR profile required', 400);
    }
    const data = await dashboardService.getStats(
      req.currentUser.hr_manager_id,
      isAdmin
    );
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

module.exports = { stats };
