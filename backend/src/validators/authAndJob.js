'use strict';

const { body } = require('express-validator');

const registerRules = [
  body('email').isEmail().withMessage('Valid email required').normalizeEmail(),
  body('password')
    .isLength({ min: 8 })
    .withMessage('Password must be at least 8 characters'),
  body('fullName').trim().notEmpty().withMessage('Full name required'),
  body('company').optional().trim(),
  body('phone').optional().trim(),
  body('role').optional().isIn(['hr', 'admin', 'candidate']).withMessage('Invalid role'),
];

const loginRules = [
  body('email').isEmail().withMessage('Valid email required').normalizeEmail(),
  body('password').notEmpty().withMessage('Password required'),
];

const jobRules = [
  body('title').trim().notEmpty().withMessage('Title required'),
  body('description').trim().notEmpty().withMessage('Description required'),
  body('requiredSkills').optional().isArray(),
  body('minimumExperience').optional().isFloat({ min: 0 }),
  body('educationLevel').optional().trim(),
  body('industry').optional().trim(),
  body('requiredCertifications').optional().isArray(),
  body('rankingWeights').optional().isObject(),
  body('communicationImportance').optional().isFloat({ min: 0, max: 1 }),
  body('status').optional().isIn(['draft', 'active', 'closed']),
];

module.exports = { registerRules, loginRules, jobRules };
