'use strict';

/**
 * Unit-style tests that do not require MySQL/AI (validators + response helpers).
 * Integration tests needing DB are skipped when DB is unavailable.
 */
const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const request = require('supertest');

process.env.JWT_SECRET = process.env.JWT_SECRET || 'test-secret';
process.env.DB_NAME = process.env.DB_NAME || 'cv_screening';

const app = require('../src/app');
const { hashPassword, comparePassword } = require('../src/utils/password');
const { signToken } = require('../src/middlewares/auth');

describe('password utils', () => {
  it('hashes and verifies password', async () => {
    const hash = await hashPassword('Password123!');
    assert.equal(await comparePassword('Password123!', hash), true);
    assert.equal(await comparePassword('wrong', hash), false);
  });
});

describe('jwt', () => {
  it('signs a token', () => {
    const token = signToken({
      id: 'u1',
      email: 'a@b.com',
      role: 'hr',
    });
    assert.ok(typeof token === 'string' && token.length > 20);
  });
});

describe('HTTP smoke', () => {
  it('GET / returns service info', async () => {
    const res = await request(app).get('/');
    assert.equal(res.status, 200);
    assert.equal(res.body.service, 'CV Screening Backend');
  });

  it('GET /api/health returns structured payload', async () => {
    const res = await request(app).get('/api/health');
    assert.ok([200, 503].includes(res.status));
    assert.ok(res.body.data);
    assert.ok('database' in res.body.data);
    assert.ok('ai' in res.body.data);
  });

  it('POST /api/auth/login validates body', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'not-an-email' });
    assert.equal(res.status, 400);
    assert.equal(res.body.success, false);
  });

  it('protected routes require auth', async () => {
    const res = await request(app).get('/api/jobs');
    assert.equal(res.status, 401);
  });
});
