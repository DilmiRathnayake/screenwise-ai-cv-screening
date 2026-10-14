'use strict';

const express = require('express');
const candidateController = require('../controllers/candidateController');
const { authenticate, authorize } = require('../middlewares/auth');

const router = express.Router();

const authCandidate = [authenticate, authorize('candidate')];

router.get('/dashboard', ...authCandidate, candidateController.dashboard);
router.get('/applications', ...authCandidate, candidateController.applications);
router.get('/interviews', ...authCandidate, candidateController.interviews);
router.get('/profile', ...authCandidate, candidateController.profile);

module.exports = router;
