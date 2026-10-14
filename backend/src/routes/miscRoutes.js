'use strict';

const express = require('express');
const cvController = require('../controllers/cvController');
const healthController = require('../controllers/healthController');
const dashboardController = require('../controllers/dashboardController');
const phase45Controller = require('../controllers/phase45Controller');
const {
  authenticate,
  authorize,
  attachHrProfile,
} = require('../middlewares/auth');

const router = express.Router();

const authHr = [authenticate, authorize('admin', 'hr'), attachHrProfile];

router.get('/dashboard/stats', ...authHr, dashboardController.stats);

router.get('/candidates/:id', ...authHr, cvController.getCandidate);

router.get('/ranking/industries', authenticate, healthController.industries);
router.get(
  '/ranking/weights/:industry',
  authenticate,
  healthController.weights
);
router.get('/ranking/model2/metrics', healthController.model2Metrics);

// Phase 4 — semantic search
router.post('/search', ...authHr, phase45Controller.search);
router.post('/search/sync', ...authHr, phase45Controller.syncIndex);

// Phase 5 — interviews & notifications
router.get('/interviews', ...authHr, phase45Controller.listInterviews);
router.post('/interviews', ...authHr, phase45Controller.schedule);
router.post('/interviews/:id/reschedule', ...authHr, phase45Controller.reschedule);
router.post('/interviews/:id/cancel', ...authHr, phase45Controller.cancel);
router.get('/notifications', ...authHr, phase45Controller.notifications);

module.exports = router;
