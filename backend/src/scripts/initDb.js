'use strict';

/**
 * Initialize database schema + seed.
 * Usage: npm run db:init
 */
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');
const config = require('../config');

async function migrateCandidateRole(connection) {
  await connection.query('USE cv_screening');
  await connection.query(
    `ALTER TABLE users
     MODIFY role ENUM('admin', 'hr', 'candidate') NOT NULL DEFAULT 'hr'`
  );
}

async function seedUsers(connection) {
  const passwordHash = await bcrypt.hash('Password123!', 10);
  await connection.query('USE cv_screening');
  await connection.query(
    `INSERT INTO users (id, email, password_hash, role, is_active) VALUES
      ('11111111-1111-1111-1111-111111111111', 'admin@cvscreening.local', ?, 'admin', 1),
      ('22222222-2222-2222-2222-222222222222', 'hr@cvscreening.local', ?, 'hr', 1),
      ('44444444-4444-4444-4444-444444444444', 'candidate@cvscreening.local', ?, 'candidate', 1)
     ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash), email = VALUES(email)`,
    [passwordHash, passwordHash, passwordHash]
  );
  await connection.query(
    `INSERT INTO hr_managers (id, user_id, full_name, company, phone) VALUES
      ('33333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222',
       'Sample HR Manager', 'Demo Recruitment Ltd', '+94 77 000 0000')
     ON DUPLICATE KEY UPDATE full_name = VALUES(full_name)`
  );
}

async function main() {
  const schemaPath = path.join(__dirname, '../../sql/schema.sql');
  const force = process.env.DB_FORCE_RESET === 'true';

  console.log('Connecting to MySQL...', {
    host: config.db.host,
    user: config.db.user,
    database: '(creating)',
  });

  const connection = await mysql.createConnection({
    host: config.db.host,
    port: config.db.port,
    user: config.db.user,
    password: config.db.password,
    multipleStatements: true,
  });

  try {
    await connection.query(
      `CREATE DATABASE IF NOT EXISTS cv_screening
       CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`
    );
    await connection.query('USE cv_screening');

    const [tables] = await connection.query(
      `SELECT TABLE_NAME FROM information_schema.TABLES
       WHERE TABLE_SCHEMA = 'cv_screening' AND TABLE_NAME = 'users'`
    );

    if (tables.length && !force) {
      console.log('Schema already present — skipping DROP/CREATE (set DB_FORCE_RESET=true to wipe).');
      await migrateCandidateRole(connection);
      console.log('Candidate role migration applied.');
      await seedUsers(connection);
      console.log('Seed upserted.');
    } else {
      const schemaSql = fs.readFileSync(schemaPath, 'utf8');
      await connection.query(schemaSql);
      console.log('Schema applied.');
      await seedUsers(connection);
      console.log('Seed applied.');
    }

    console.log('Login credentials:');
    console.log('  admin@cvscreening.local / Password123!');
    console.log('  hr@cvscreening.local / Password123!');
    console.log('  candidate@cvscreening.local / Password123!');
  } finally {
    await connection.end();
  }
}

main().catch((err) => {
  console.error('DB init failed:', err.message);
  process.exit(1);
});
