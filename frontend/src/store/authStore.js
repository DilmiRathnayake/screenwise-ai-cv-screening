const TOKEN_KEY = 'cv_screening_token';
const USER_KEY = 'cv_screening_user';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

const KNOWN_ROLES = ['admin', 'hr', 'candidate'];

// A token alone is not a session: guards redirect by the stored user's role, so a
// token without a valid user (corrupt/partial storage) would redirect /login to
// itself forever and leave a blank page. Treat that state as logged out and clear it.
export function isAuthenticated() {
  if (!getToken()) return false;
  const user = getStoredUser();
  if (user && KNOWN_ROLES.includes(user.role)) return true;
  clearAuth();
  return false;
}

export function homePathForUser(user) {
  if (!user) return '/login';
  if (user.role === 'admin') return '/admin';
  if (user.role === 'candidate') return '/candidate';
  return '/hr';
}
