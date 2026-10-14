'use strict';

const fs = require('fs');
const path = require('path');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
const config = require('../config');
const { AppError } = require('./errorHandler');

const ALLOWED_EXT = new Set(['.pdf', '.docx', '.png', '.jpg', '.jpeg']);
const ALLOWED_MIME = new Set([
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'image/png',
  'image/jpeg',
]);

if (!fs.existsSync(config.upload.dir)) {
  fs.mkdirSync(config.upload.dir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, config.upload.dir),
  filename: (_req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, `${Date.now()}-${uuidv4()}${ext}`);
  },
});

function fileFilter(_req, file, cb) {
  const ext = path.extname(file.originalname).toLowerCase();
  if (!ALLOWED_EXT.has(ext)) {
    return cb(new AppError(`Unsupported file type: ${ext}`, 400));
  }
  if (file.mimetype && !ALLOWED_MIME.has(file.mimetype) && file.mimetype !== 'application/octet-stream') {
    return cb(new AppError(`Unsupported MIME type: ${file.mimetype}`, 400));
  }
  return cb(null, true);
}

const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: config.upload.maxUploadMb * 1024 * 1024,
    files: config.upload.maxBulkFiles,
  },
});

module.exports = { upload, ALLOWED_EXT };
