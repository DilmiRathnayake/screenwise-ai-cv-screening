import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { authApi, queryKeys } from '../../api/endpoints';
import { useTheme } from '../../lib/theme';
import { getStoredUser } from '../../store/authStore';
import { Button } from '../../components/ui/button';
import { Card, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Switch } from '../../components/ui/switch';
import { UserAvatar } from '../../components/ui/avatar';
import { PageHeader, Spinner } from '../../components/ui/misc';
import { useEffect, useState } from 'react';

const PREFS_KEY = 'screenwise_notif_prefs';

export default function SettingsPage() {
  const user = getStoredUser();
  const { theme, setTheme } = useTheme();
  const meQuery = useQuery({
    queryKey: queryKeys.me,
    queryFn: authApi.me,
    enabled: user?.role !== 'candidate',
  });
  const me = meQuery.data?.data || user;

  const [prefs, setPrefs] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(PREFS_KEY) || '{}');
    } catch {
      return {};
    }
  });

  useEffect(() => {
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  }, [prefs]);

  return (
    <div>
      <PageHeader title="Settings" subtitle="Theme, profile, and notification preferences." />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Profile</CardTitle>
          {meQuery.isLoading ? (
            <Spinner className="py-8" />
          ) : (
            <div className="mt-4 flex items-center gap-4">
              <UserAvatar name={me?.full_name || me?.email || 'User'} size="xl" />
              <div className="space-y-1">
                <p className="font-semibold">{me?.full_name || me?.hr_manager?.full_name || '—'}</p>
                <p className="text-sm text-muted-foreground">{me?.email}</p>
                <p className="text-xs capitalize text-muted-foreground">{me?.role}</p>
              </div>
            </div>
          )}
          <div className="mt-5 space-y-3">
            <Input label="Display name" defaultValue={me?.full_name || ''} readOnly />
            <Input label="Email" defaultValue={me?.email || ''} readOnly />
            <Button
              variant="secondary"
              onClick={() => toast('Demo — password change requires backend support', { icon: '🔒' })}
            >
              Change password
            </Button>
          </div>
        </Card>

        <Card>
          <CardTitle>Appearance</CardTitle>
          <div className="mt-4 grid grid-cols-3 gap-2">
            {[
              { id: 'light', label: 'Light' },
              { id: 'dark', label: 'Dark' },
              { id: 'system', label: 'System' },
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTheme(t.id)}
                className={`rounded-xl border px-3 py-3 text-sm font-semibold transition ${
                  theme === t.id
                    ? 'border-accent bg-[var(--sw-accent-soft)] text-accent'
                    : 'border-border hover:bg-muted'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <CardTitle className="mt-8">Notifications</CardTitle>
          <div className="mt-4 space-y-4">
            {[
              { key: 'interviews', label: 'Interview reminders' },
              { key: 'rankings', label: 'Ranking completed' },
              { key: 'uploads', label: 'CV upload results' },
            ].map((p) => (
              <div key={p.key} className="flex items-center justify-between gap-3">
                <span className="text-sm">{p.label}</span>
                <Switch
                  checked={prefs[p.key] !== false}
                  onCheckedChange={(v) => setPrefs((s) => ({ ...s, [p.key]: v }))}
                />
              </div>
            ))}
          </div>

          <CardTitle className="mt-8">Security</CardTitle>
          <p className="mt-2 text-sm text-muted-foreground">
            Sessions are JWT-based. Signing out clears local credentials.
          </p>
        </Card>
      </div>
    </div>
  );
}
