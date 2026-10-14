import { useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Bell,
  Briefcase,
  CalendarDays,
  ChevronLeft,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Search,
  Settings,
  Sparkles,
  Sun,
  Monitor,
  FileBarChart,
  Activity,
  Users,
  X,
} from 'lucide-react';
import { notificationsApi, queryKeys } from '../../api/endpoints';
import { clearAuth, getStoredUser } from '../../store/authStore';
import { useTheme } from '../../lib/theme';
import { cn } from '../../lib/utils';
import { Button } from '../ui/button';
import { UserAvatar } from '../ui/avatar';
import { PageTransition } from '../motion/PageTransition';

const HR_NAV = [
  { to: '/hr', end: true, label: 'Overview', icon: LayoutDashboard },
  { to: '/hr/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/hr/search', label: 'AI Search', icon: Search },
  { to: '/hr/interviews', label: 'Calendar', icon: CalendarDays },
  { to: '/hr/reports', label: 'Reports', icon: FileBarChart },
  { to: '/hr/notifications', label: 'Alerts', icon: Bell },
  { to: '/hr/settings', label: 'Settings', icon: Settings },
];

const ADMIN_NAV = [
  { to: '/admin', end: true, label: 'Command', icon: LayoutDashboard },
  { to: '/admin/health', label: 'System', icon: Activity },
  { to: '/admin/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/admin/search', label: 'AI Search', icon: Search },
  { to: '/admin/interviews', label: 'Calendar', icon: CalendarDays },
  { to: '/admin/users', label: 'People', icon: Users },
  { to: '/admin/settings', label: 'Settings', icon: Settings },
];

const CANDIDATE_NAV = [
  { to: '/candidate', end: true, label: 'Home', icon: LayoutDashboard },
  { to: '/candidate/applications', label: 'Applications', icon: Briefcase },
  { to: '/candidate/calendar', label: 'Interviews', icon: CalendarDays },
  { to: '/candidate/profile', label: 'Profile', icon: Users },
  { to: '/candidate/settings', label: 'Settings', icon: Settings },
];

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const Icon = theme === 'dark' ? Moon : theme === 'light' ? Sun : Monitor;
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Toggle theme"
      onClick={() =>
        setTheme(theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light')
      }
      title={`Theme: ${theme}`}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}

export default function AppShell({ variant = 'hr' }) {
  const user = getStoredUser();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const nav = variant === 'admin' ? ADMIN_NAV : variant === 'candidate' ? CANDIDATE_NAV : HR_NAV;
  const brandSub =
    variant === 'admin' ? 'Admin' : variant === 'candidate' ? 'Candidate' : 'Recruiting';

  const notifQuery = useQuery({
    queryKey: queryKeys.notifications,
    queryFn: notificationsApi.list,
    enabled: variant !== 'candidate',
    refetchInterval: 60_000,
  });
  const unread = useMemo(() => {
    const list = notifQuery.data?.data || [];
    return list.filter((n) => !n.read_at && !n.is_read).length || list.length;
  }, [notifQuery.data]);

  useEffect(() => {
    setMobileOpen(false);
  }, []);

  function logout() {
    clearAuth();
    navigate('/login');
  }

  const sidebar = (
    <aside
      className={cn(
        'glass flex h-full flex-col border-r border-border transition-all duration-300',
        collapsed ? 'w-[76px]' : 'w-[260px]'
      )}
    >
      <div className="flex items-center gap-3 px-4 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-accent-foreground shadow-lg shadow-accent/30">
          <Sparkles className="h-5 w-5" />
        </div>
        {!collapsed ? (
          <div className="min-w-0">
            <p className="truncate font-display text-lg font-semibold leading-none">ScreenWise</p>
            <p className="mt-1 text-xs text-muted-foreground">{brandSub}</p>
          </div>
        ) : null}
      </div>

      <nav className="flex-1 space-y-1 px-2 pb-4">
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                'group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground',
                isActive && 'bg-[var(--sw-accent-soft)] text-accent'
              )
            }
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed ? <span>{item.label}</span> : null}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        <div className={cn('flex items-center gap-3 rounded-xl p-2', collapsed && 'justify-center')}>
          <UserAvatar name={user?.full_name || user?.email || 'User'} />
          {!collapsed ? (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{user?.full_name || user?.email}</p>
              <p className="truncate text-xs capitalize text-muted-foreground">{user?.role}</p>
            </div>
          ) : null}
        </div>
        <Button
          variant="ghost"
          className={cn('mt-1 w-full justify-start text-muted-foreground', collapsed && 'px-0 justify-center')}
          onClick={logout}
        >
          <LogOut className="h-4 w-4" />
          {!collapsed ? 'Sign out' : null}
        </Button>
      </div>
    </aside>
  );

  return (
    <div className="flex min-h-screen">
      <div className="hidden md:block">{sidebar}</div>

      <AnimatePresence>
        {mobileOpen ? (
          <motion.div
            className="fixed inset-0 z-50 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <button
              className="absolute inset-0 bg-black/50"
              aria-label="Close menu"
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              className="absolute inset-y-0 left-0 w-[280px]"
            >
              {sidebar}
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-border bg-background/70 px-4 backdrop-blur-xl md:px-6">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="hidden md:inline-flex"
              onClick={() => setCollapsed((c) => !c)}
              aria-label="Collapse sidebar"
            >
              {collapsed ? <Menu className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </Button>
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground md:hidden">
              ScreenWise
            </Link>
          </div>

          <div className="flex items-center gap-1">
            {variant !== 'candidate' ? (
              <Button
                variant="ghost"
                size="icon"
                className="relative"
                onClick={() => navigate(`/${variant === 'admin' ? 'admin' : 'hr'}/notifications`)}
                aria-label="Notifications"
              >
                <Bell className="h-4 w-4" />
                {unread > 0 ? (
                  <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-accent" />
                ) : null}
              </Button>
            ) : null}
            <ThemeToggle />
            <Button variant="ghost" size="icon" className="md:hidden" onClick={logout} aria-label="Sign out">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 md:px-8 md:py-8">
          <PageTransition>
            <Outlet />
          </PageTransition>
        </main>
      </div>
    </div>
  );
}
