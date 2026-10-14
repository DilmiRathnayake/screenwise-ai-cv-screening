'use strict';

require('dotenv').config();

const path = require('path');

const isProd = process.env.NODE_ENV === 'production';
const jwtSecret = process.env.JWT_SECRET || '';

if (isProd) {
  if (!jwtSecret || jwtSecret === 'dev-secret' || jwtSecret.length < 16) {
    console.error(
      'FATAL: JWT_SECRET must be set to a strong unique value (≥16 chars) when NODE_ENV=production'
    );
    process.exit(1);
  }
}

const config = {
  port: Number(process.env.PORT || 5000),
  nodeEnv: process.env.NODE_ENV || 'development',
  isProd,
  db: {
    host: process.env.DB_HOST || '127.0.0.1',
    port: Number(process.env.DB_PORT || 3306),
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'cv_screening',
  },
  jwt: {
    secret: jwtSecret || 'dev-secret',
    expiresIn: process.env.JWT_EXPIRES_IN || '8h',
  },
  ai: {
    baseUrl: (process.env.AI_SERVICE_URL || 'http://localhost:8000').replace(/\/$/, ''),
    timeoutMs: Number(process.env.AI_TIMEOUT_MS || 120000),
  },
  upload: {
    dir: path.resolve(
      __dirname,
      '..',
      '..',
      process.env.UPLOAD_DIR || 'uploads/cvs'
    ),
    maxUploadMb: Number(process.env.MAX_UPLOAD_MB || 25),
    maxBulkFiles: Number(process.env.MAX_BULK_FILES || 100),
  },
  shortlistTopFraction: Number(process.env.SHORTLIST_TOP_FRACTION || 0.1),
  corsOrigins: (process.env.CORS_ORIGINS || 'http://localhost:5173')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
  n8n: {
    webhookUrl: process.env.N8N_WEBHOOK_URL || '',
  },
  sendgrid: {
    apiKey: process.env.SENDGRID_API_KEY || '',
    fromEmail: process.env.SENDGRID_FROM_EMAIL || 'noreply@cvscreening.local',
  },
  google: {
    calendarEnabled: process.env.GOOGLE_CALENDAR_ENABLED === 'true',
  },
};

module.exports = config;
