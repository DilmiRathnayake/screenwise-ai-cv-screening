'use strict';

const fs = require('fs');
const app = require('./app');
const config = require('./config');
const logger = require('./utils/logger');
const { closePool } = require('./config/db');

if (!fs.existsSync(config.upload.dir)) {
  fs.mkdirSync(config.upload.dir, { recursive: true });
}

const server = app.listen(config.port, () => {
  logger.info(`Backend listening on http://localhost:${config.port}`);
  logger.info(`AI service URL: ${config.ai.baseUrl}`);
});

async function shutdown(signal) {
  logger.info(`${signal} received — shutting down`);
  server.close(async () => {
    await closePool();
    process.exit(0);
  });
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));
