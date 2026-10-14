'use strict';

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');

(async () => {
  const connection = await mysql.createConnection({
    host: process.env.DB_HOST || '127.0.0.1',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    multipleStatements: true,
  });
  const sql = fs.readFileSync(
    path.join(__dirname, '../../sql/migration_phase4_5.sql'),
    'utf8'
  );
  await connection.query(sql);
  console.log('Phase 4/5 migration applied');
  await connection.end();
})().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
