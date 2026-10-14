'use strict';

const { validationResult } = require('express-validator');
const { AppError } = require('./errorHandler');

function validate(req, res, next) {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return next(
      new AppError('Validation failed', 400, errors.array().map((e) => ({
        field: e.path,
        message: e.msg,
      })))
    );
  }
  return next();
}

module.exports = { validate };
