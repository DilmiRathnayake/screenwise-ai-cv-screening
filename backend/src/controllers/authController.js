'use strict';

const authService = require('../services/authService');
const { success } = require('../utils/response');

async function register(req, res, next) {
  try {
    const data = await authService.register(req.body, req.user);
    return success(res, data, 'Registered successfully', 201);
  } catch (err) {
    return next(err);
  }
}

async function login(req, res, next) {
  try {
    const data = await authService.login(req.body);
    return success(res, data, 'Login successful');
  } catch (err) {
    return next(err);
  }
}

async function me(req, res, next) {
  try {
    const data = await authService.me(req.user.id);
    return success(res, data);
  } catch (err) {
    return next(err);
  }
}

module.exports = { register, login, me };
