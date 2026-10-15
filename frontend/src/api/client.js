import axios from 'axios';
import { clearAuth, getToken } from '../store/authStore';

// Empty / unset → same-origin (Vite proxy in dev, nginx /api proxy in Docker)
const apiBase =
  import.meta.env.VITE_API_URL !== undefined && import.meta.env.VITE_API_URL !== null
    ? import.meta.env.VITE_API_URL
    : '';

const api = axios.create({
  baseURL: apiBase,
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      clearAuth();
      if (!window.location.pathname.startsWith('/login')) {
        window.location.assign('/login');
      }
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(error) {
  if (error?.request && !error?.response) {
    return 'Cannot reach the server. Please check that the backend is running.';
  }
  return (
    error?.response?.data?.message ||
    error?.message ||
    'Something went wrong'
  );
}

export default api;
