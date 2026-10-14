'use strict';

const config = require('../config');
const logger = require('../utils/logger');

function notFoundHandler(req, res) {
  res.status(404).json({
    success: false,
    message: `Route not found: ${req.method} ${req.originalUrl}`,
  });
}

function errorHandler(err, req, res, next) {
  const status = err.status || err.statusCode || 500;
  if (status >= 500) {
    logger.error(err.message, { stack: err.stack });
  } else {
    logger.warn(err.message);
  }

  const message =
    status >= 500 && config.isProd
      ? 'Internal server error'
      : err.message || 'Internal server error';

  res.status(status).json({
    success: false,
    message,
    ...(err.details ? { details: err.details } : {}),
  });
}

class AppError extends Error {
  constructor(message, status = 400, details = null) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

module.exports = { notFoundHandler, errorHandler, AppError };
