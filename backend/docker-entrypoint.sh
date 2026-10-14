#!/bin/sh
set -e

echo "Waiting for MySQL at ${DB_HOST:-mysql}:${DB_PORT:-3306}..."
i=0
until node -e "
const mysql = require('mysql2/promise');
(async () => {
  const c = await mysql.createConnection({
    host: process.env.DB_HOST || 'mysql',
    port: Number(process.env.DB_PORT || 3306),
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
  });
  await c.ping();
  await c.end();
})().catch(() => process.exit(1));
"; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "MySQL did not become ready in time"
    exit 1
  fi
  sleep 2
done

echo "MySQL is up â€” initializing schema/seed (idempotent)..."
node src/scripts/initDb.js
node src/scripts/migratePhase45.js || true

echo "Starting backend..."
exec node src/server.js
