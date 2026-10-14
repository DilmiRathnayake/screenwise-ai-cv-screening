'use strict';

const express = require('express');
const cors = require('cors');
const config = require('./config');
const logger = require('./utils/logger');
const authRoutes = require('./routes/authRoutes');
const jobRoutes = require('./routes/jobRoutes');
const candidateRoutes = require('./routes/candidateRoutes');
const miscRoutes = require('./routes/miscRoutes');
const healthController = require('./controllers/healthController');
const {
  notFoundHandler,
  errorHandler,
} = require('./middlewares/errorHandler');

const app = express();

app.use(
  cors({
    origin: config.corsOrigins,
    credentials: true,
  })
);
app.use(express.json({ limit: '2mb' }));
app.use(express.urlencoded({ extended: true }));

app.get('/', (_req, res) => {
  res.json({
    service: 'CV Screening Backend',
    version: '1.0.0',
    health: '/api/health',
  });
});

app.get('/api/health', healthController.health);
app.use('/api/auth', authRoutes);
app.use('/api/jobs', jobRoutes);
app.use('/api/candidate', candidateRoutes);
app.use('/api', miscRoutes);

app.use(notFoundHandler);
app.use(errorHandler);

logger.info('Express app configured');

module.exports = app;
