'use strict';

const axios = require('axios');
const FormData = require('form-data');
const config = require('../config');
const logger = require('../utils/logger');
const { AppError } = require('../middlewares/errorHandler');

class AiServiceClient {
  constructor() {
    this.client = axios.create({
      baseURL: config.ai.baseUrl,
      timeout: config.ai.timeoutMs,
    });
  }

  async health() {
    const { data } = await this.client.get('/api/v1/health');
    return data;
  }

  async extract(fileBuffer, filename) {
    const form = new FormData();
    form.append('file', fileBuffer, { filename });
    try {
      const { data } = await this.client.post('/api/v1/extract', form, {
        headers: form.getHeaders(),
        maxBodyLength: Infinity,
      });
      return data;
    } catch (err) {
      throw this._wrap(err, 'AI extraction failed');
    }
  }

  async extractBulk(files) {
    const form = new FormData();
    for (const f of files) {
      form.append('files', f.buffer, { filename: f.filename });
    }
    try {
      const { data } = await this.client.post('/api/v1/extract/bulk', form, {
        headers: form.getHeaders(),
        maxBodyLength: Infinity,
      });
      return data;
    } catch (err) {
      throw this._wrap(err, 'AI bulk extraction failed');
    }
  }

  async rank(jobPayload, candidates) {
    try {
      const { data } = await this.client.post('/api/v1/rank', {
        job: jobPayload,
        candidates,
      });
      return data;
    } catch (err) {
      throw this._wrap(err, 'AI ranking failed');
    }
  }

  async getWeights(industry) {
    try {
      const { data } = await this.client.get(
        `/api/v1/ranking/weights/${encodeURIComponent(industry)}`
      );
      return data;
    } catch (err) {
      logger.warn(`AI weights fetch failed for ${industry}: ${err.message}`);
      return {
        industry: 'it',
        weights: {
          technical_skills: 0.35,
          experience: 0.25,
          education: 0.15,
          communication: 0.10,
          projects: 0.10,
          certifications: 0.05,
        },
        criteria: [
          'technical_skills',
          'experience',
          'projects',
          'education',
          'communication',
          'certifications',
        ],
      };
    }
  }

  async listIndustries() {
    try {
      const { data } = await this.client.get('/api/v1/ranking/industries');
      return data;
    } catch (err) {
      return { industries: ['it'] };
    }
  }

  async getModel2Metrics() {
    const { data } = await this.client.get('/api/v1/ranking/model2/metrics');
    return data;
  }

  async upsertEmbeddings(documents) {
    try {
      const { data } = await this.client.post('/api/v1/embeddings/upsert', {
        documents,
      });
      return data;
    } catch (err) {
      throw this._wrap(err, 'AI embedding upsert failed');
    }
  }

  async semanticSearch(query, topK = 10, filter = null) {
    try {
      const { data } = await this.client.post('/api/v1/search', {
        query,
        top_k: topK,
        filter,
      });
      return data;
    } catch (err) {
      throw this._wrap(err, 'AI semantic search failed');
    }
  }

  _wrap(err, fallbackMessage) {
    const detail =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      fallbackMessage;
    const status = err.response?.status === 400 ? 400 : 502;
    logger.error(`${fallbackMessage}: ${detail}`);
    return new AppError(detail, status);
  }
}

module.exports = new AiServiceClient();
