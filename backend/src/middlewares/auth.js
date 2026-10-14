'use strict';

const jwt = require('jsonwebtoken');
const config = require('../config');
const { AppError } = require('./errorHandler');
const userRepository = require('../repositories/userRepository');

function authenticate(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) {
    return next(new AppError('Authentication required', 401));
  }
  try {
    const payload = jwt.verify(token, config.jwt.secret);
    req.user = { id: payload.sub, email: payload.email, role: payload.role };
    return next();
  } catch {
    return next(new AppError('Invalid or expired token', 401));
  }
}

function authorize(...roles) {
  return (req, res, next) => {
    if (!req.user) return next(new AppError('Authentication required', 401));
    if (roles.length && !roles.includes(req.user.role)) {
      return next(new AppError('Insufficient permissions', 403));
    }
    return next();
  };
}

async function attachHrProfile(req, res, next) {
  try {
    const user = await userRepository.findById(req.user.id);
    if (!user) return next(new AppError('User not found', 404));
    req.currentUser = user;
    req.hrManagerId = user.hr_manager_id || null;
    return next();
  } catch (err) {
    return next(err);
  }
}

function signToken(user) {
  return jwt.sign(
    { email: user.email, role: user.role },
    config.jwt.secret,
    { subject: user.id, expiresIn: config.jwt.expiresIn }
  );
}

module.exports = {
  authenticate,
  authorize,
  attachHrProfile,
  signToken,
};
