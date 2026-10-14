import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './lib/theme';
import AppShell from './components/layout/AppShell';
import { ProtectedRoute, PublicOnlyRoute, RoleRedirect } from './routes/guards';
import LandingPage from './pages/landing/LandingPage';
import PortalChooserPage from './pages/auth/PortalChooserPage';
import RoleLoginPage from './pages/auth/RoleLoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import CandidateRegisterPage from './pages/auth/CandidateRegisterPage';
import WorkspaceDashboard from './pages/workspace/DashboardPage';
import JobsPage from './pages/workspace/JobsPage';
import JobDetailPage from './pages/workspace/JobDetailPage';
import SearchPage from './pages/workspace/SearchPage';
import InterviewsPage from './pages/workspace/InterviewsPage';
import NotificationsPage from './pages/workspace/NotificationsPage';
import SettingsPage from './pages/workspace/SettingsPage';
import ReportsPage from './pages/workspace/ReportsPage';
import AdminDashboardPage, {
  AdminHealthPage,
  AdminUsersPage,
} from './pages/admin/AdminPages';
import {
  CandidateHomePage,
  CandidateApplicationsPage,
  CandidateCalendarPage,
  CandidateProfilePage,
} from './pages/candidate/CandidatePages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 15_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />

            <Route element={<PublicOnlyRoute />}>
              <Route path="/login" element={<PortalChooserPage />} />
              <Route path="/login/admin" element={<RoleLoginPage role="admin" />} />
              <Route path="/login/hr" element={<RoleLoginPage role="hr" />} />
              <Route path="/login/candidate" element={<RoleLoginPage role="candidate" />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/register/candidate" element={<CandidateRegisterPage />} />
            </Route>

            <Route element={<ProtectedRoute roles={['hr', 'admin']} />}>
              <Route path="/hr" element={<AppShell variant="hr" />}>
                <Route index element={<WorkspaceDashboard basePath="/hr" />} />
                <Route path="jobs" element={<JobsPage basePath="/hr" />} />
                <Route path="jobs/:jobId" element={<JobDetailPage basePath="/hr" />} />
                <Route path="search" element={<SearchPage />} />
                <Route path="interviews" element={<InterviewsPage />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="notifications" element={<NotificationsPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute roles={['admin']} />}>
              <Route path="/admin" element={<AppShell variant="admin" />}>
                <Route index element={<AdminDashboardPage />} />
                <Route path="health" element={<AdminHealthPage />} />
                <Route path="users" element={<AdminUsersPage />} />
                <Route path="jobs" element={<JobsPage basePath="/admin" />} />
                <Route path="jobs/:jobId" element={<JobDetailPage basePath="/admin" />} />
                <Route path="search" element={<SearchPage />} />
                <Route path="interviews" element={<InterviewsPage />} />
                <Route path="notifications" element={<NotificationsPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute roles={['candidate']} />}>
              <Route path="/candidate" element={<AppShell variant="candidate" />}>
                <Route index element={<CandidateHomePage />} />
                <Route path="applications" element={<CandidateApplicationsPage />} />
                <Route path="calendar" element={<CandidateCalendarPage />} />
                <Route path="profile" element={<CandidateProfilePage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Route>

            <Route path="/app" element={<RoleRedirect />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'glass !bg-card !text-foreground !border !border-border',
          }}
        />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
