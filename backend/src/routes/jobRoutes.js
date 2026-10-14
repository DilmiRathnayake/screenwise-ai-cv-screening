'use strict';

const express = require('express');
const jobController = require('../controllers/jobController');
const cvController = require('../controllers/cvController');
const { jobRules } = require('../validators/authAndJob');
const { validate } = require('../middlewares/validate');
const {
  authenticate,
  authorize,
  attachHrProfile,
} = require('../middlewares/auth');
const { upload } = require('../middlewares/upload');

const router = express.Router();

router.use(authenticate, authorize('admin', 'hr'), attachHrProfile);

router.get('/', jobController.list);
router.post('/', jobRules, validate, jobController.create);
router.get('/:id', jobController.getById);
router.put('/:id', jobRules, validate, jobController.update);
router.delete('/:id', jobController.remove);
router.post('/:id/close', jobController.close);
router.post('/:id/duplicate', jobController.duplicate);

router.post('/:jobId/cvs', upload.single('file'), cvController.uploadSingle);
router.post(
  '/:jobId/cvs/bulk',
  upload.array('files', 100),
  cvController.uploadBulk
);
router.get('/:jobId/candidates', cvController.listCandidates);
router.post('/:jobId/rank', cvController.rank);
router.get('/:jobId/rankings', cvController.rankings);
router.get('/:jobId/interviews', (req, res, next) => {
  req.params.jobId = req.params.jobId;
  return require('../controllers/phase45Controller').listInterviews(req, res, next);
});

module.exports = router;
