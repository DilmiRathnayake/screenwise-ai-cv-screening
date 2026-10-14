import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { getStoredUser, isAuthenticated, homePathForUser } from '../store/authStore';

export function ProtectedRoute({ roles }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  const user = getStoredUser();
  if (roles?.length && user && !roles.includes(user.role)) {
    return <Navigate to={homePathForUser(user)} replace />;
  }
  return <Outlet />;
}

export function PublicOnlyRoute() {
  if (isAuthenticated()) {
    const user = getStoredUser();
    return <Navigate to={homePathForUser(user)} replace />;
  }
  return <Outlet />;
}

export function RoleRedirect() {
  const user = getStoredUser();
  if (!isAuthenticated()) return <Navigate to="/login" replace />;
  return <Navigate to={homePathForUser(user)} replace />;
}

export function RequireAuth({ children, roles }) {
  const location = useLocation();
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  const user = getStoredUser();
  if (roles?.length && !roles.includes(user?.role)) {
    return <Navigate to={homePathForUser(user)} replace />;
  }
  return children;
}
