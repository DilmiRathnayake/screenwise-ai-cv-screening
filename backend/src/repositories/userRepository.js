'use strict';

const { v4: uuidv4 } = require('uuid');
const { query } = require('../config/db');

async function findByEmail(email) {
  const rows = await query(
    'SELECT id, email, password_hash, role, is_active, created_at FROM users WHERE email = ? LIMIT 1',
    [email]
  );
  return rows[0] || null;
}

async function findById(id) {
  const rows = await query(
    `SELECT u.id, u.email, u.role, u.is_active, u.created_at,
            h.id AS hr_manager_id, h.full_name, h.company, h.phone
     FROM users u
     LEFT JOIN hr_managers h ON h.user_id = u.id
     WHERE u.id = ?
     LIMIT 1`,
    [id]
  );
  return rows[0] || null;
}

async function createUser({ email, passwordHash, role }) {
  const id = uuidv4();
  await query(
    'INSERT INTO users (id, email, password_hash, role) VALUES (?, ?, ?, ?)',
    [id, email, passwordHash, role]
  );
  return id;
}

async function createHrProfile({ userId, fullName, company, phone }) {
  const id = uuidv4();
  await query(
    'INSERT INTO hr_managers (id, user_id, full_name, company, phone) VALUES (?, ?, ?, ?, ?)',
    [id, userId, fullName, company || null, phone || null]
  );
  return id;
}

module.exports = {
  findByEmail,
  findById,
  createUser,
  createHrProfile,
};
