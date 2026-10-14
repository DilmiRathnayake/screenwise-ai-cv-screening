'use strict';

const userRepository = require('../repositories/userRepository');
const candidateRepository = require('../repositories/candidateRepository');
const { hashPassword, comparePassword } = require('../utils/password');
const { signToken } = require('../middlewares/auth');
const { AppError } = require('../middlewares/errorHandler');

async function register({ email, password, fullName, company, phone, role }, actor) {
  const existing = await userRepository.findByEmail(email);
  if (existing) throw new AppError('Email already registered', 409);

  const requestedRole = role || 'hr';
  if (requestedRole === 'admin') {
    if (!actor || actor.role !== 'admin') {
      throw new AppError('Only admins can create admin accounts', 403);
    }
  }

  const passwordHash = await hashPassword(password);
  const userId = await userRepository.createUser({
    email,
    passwordHash,
    role: requestedRole,
  });

  let hrManagerId = null;
  if (requestedRole === 'hr') {
    hrManagerId = await userRepository.createHrProfile({
      userId,
      fullName,
      company,
      phone,
    });
  }
  if (requestedRole === 'candidate') {
    await candidateRepository.ensureStubForUser({ email, fullName });
  }

  const user = await userRepository.findById(userId);
  const token = signToken({ id: userId, email, role: requestedRole });
  return {
    token,
    user: sanitize(user),
    hrManagerId,
  };
}

async function login({ email, password }) {
  const user = await userRepository.findByEmail(email);
  if (!user || !user.is_active) {
    throw new AppError('Invalid email or password', 401);
  }
  const ok = await comparePassword(password, user.password_hash);
  if (!ok) throw new AppError('Invalid email or password', 401);

  const full = await userRepository.findById(user.id);
  const token = signToken(user);
  return { token, user: sanitize(full) };
}

async function me(userId) {
  const user = await userRepository.findById(userId);
  if (!user) throw new AppError('User not found', 404);
  return sanitize(user);
}

function sanitize(user) {
  return {
    id: user.id,
    email: user.email,
    role: user.role,
    is_active: !!user.is_active,
    hr_manager_id: user.hr_manager_id || null,
    full_name: user.full_name || null,
    company: user.company || null,
    phone: user.phone || null,
    created_at: user.created_at,
  };
}

module.exports = { register, login, me };
