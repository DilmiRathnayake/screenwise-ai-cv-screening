import api from './client';

export const authApi = {
  login: (payload) => api.post('/api/auth/login', payload).then((r) => r.data),
  register: (payload) =>
    api.post('/api/auth/register', payload).then((r) => r.data),
  me: () => api.get('/api/auth/me').then((r) => r.data),
};

export const dashboardApi = {
  stats: () => api.get('/api/dashboard/stats').then((r) => r.data),
};

export const jobsApi = {
  list: () => api.get('/api/jobs').then((r) => r.data),
  get: (id) => api.get(`/api/jobs/${id}`).then((r) => r.data),
  create: (payload) => api.post('/api/jobs', payload).then((r) => r.data),
  update: (id, payload) =>
    api.put(`/api/jobs/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/api/jobs/${id}`).then((r) => r.data),
  close: (id) => api.post(`/api/jobs/${id}/close`).then((r) => r.data),
  duplicate: (id) =>
    api.post(`/api/jobs/${id}/duplicate`).then((r) => r.data),
  candidates: (jobId) =>
    api.get(`/api/jobs/${jobId}/candidates`).then((r) => r.data),
  rankings: (jobId) =>
    api.get(`/api/jobs/${jobId}/rankings`).then((r) => r.data),
  rank: (jobId) => api.post(`/api/jobs/${jobId}/rank`).then((r) => r.data),
  uploadCv: (jobId, file) => {
    const form = new FormData();
    form.append('file', file);
    return api
      .post(`/api/jobs/${jobId}/cvs`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data);
  },
  uploadBulk: (jobId, files) => {
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    return api
      .post(`/api/jobs/${jobId}/cvs/bulk`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data);
  },
};

export const candidatesApi = {
  get: (id) => api.get(`/api/candidates/${id}`).then((r) => r.data),
};

export const candidatePortalApi = {
  dashboard: () => api.get('/api/candidate/dashboard').then((r) => r.data),
  applications: () => api.get('/api/candidate/applications').then((r) => r.data),
  interviews: () => api.get('/api/candidate/interviews').then((r) => r.data),
  profile: () => api.get('/api/candidate/profile').then((r) => r.data),
};

export const rankingApi = {
  industries: () =>
    api.get('/api/ranking/industries').then((r) => r.data),
  weights: (industry) =>
    api.get(`/api/ranking/weights/${industry}`).then((r) => r.data),
  model2Metrics: () =>
    api.get('/api/ranking/model2/metrics').then((r) => r.data),
};

export const searchApi = {
  search: (query, topK = 10) =>
    api.post('/api/search', { query, topK }).then((r) => r.data),
  sync: () => api.post('/api/search/sync').then((r) => r.data),
};

export const interviewsApi = {
  list: () => api.get('/api/interviews').then((r) => r.data),
  listByJob: (jobId) =>
    api.get(`/api/jobs/${jobId}/interviews`).then((r) => r.data),
  schedule: (payload) =>
    api.post('/api/interviews', payload).then((r) => r.data),
  reschedule: (id, payload) =>
    api.post(`/api/interviews/${id}/reschedule`, payload).then((r) => r.data),
  cancel: (id) =>
    api.post(`/api/interviews/${id}/cancel`).then((r) => r.data),
};

export const notificationsApi = {
  list: () => api.get('/api/notifications').then((r) => r.data),
};

export const queryKeys = {
  me: ['me'],
  stats: ['dashboard', 'stats'],
  jobs: ['jobs'],
  job: (id) => ['jobs', id],
  candidates: (jobId) => ['jobs', jobId, 'candidates'],
  rankings: (jobId) => ['jobs', jobId, 'rankings'],
  candidate: (id) => ['candidates', id],
  candidateDashboard: ['candidate', 'dashboard'],
  candidateApplications: ['candidate', 'applications'],
  candidateInterviews: ['candidate', 'interviews'],
  candidateProfile: ['candidate', 'profile'],
  industries: ['industries'],
  weights: (industry) => ['weights', industry],
  model2Metrics: ['ranking', 'model2', 'metrics'],
  interviews: ['interviews'],
  notifications: ['notifications'],
};
