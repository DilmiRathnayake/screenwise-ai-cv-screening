'use strict';

const express = require('express');
const authController = require('../controllers/authController');
const { registerRules, loginRules } = require('../validators/authAndJob');
const { validate } = require('../middlewares/validate');
const { authenticate, authorize } = require('../middlewares/auth');

const router = express.Router();

router.post('/register', registerRules, validate, authController.register);
router.post('/login', loginRules, validate, authController.login);
router.get('/me', authenticate, authorize('admin', 'hr'), authController.me);

module.exports = router;
