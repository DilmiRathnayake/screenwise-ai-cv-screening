import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, Cpu, Database, HardDrive, Server, Users } from 'lucide-react';
import { dashboardApi, interviewsApi, jobsApi, queryKeys } from '../../api/endpoints';
import { AreaTrend, DonutChart, LinesChart } from '../../components/charts/Charts';
import { Badge } from '../../components/ui/badge';
import { Card, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';
import { PageHeader, Skeleton } from '../../components/ui/misc';
import api from '../../api/client';

const DEMO_GAUGES = [
  { label: 'Server CPU', value: 42, icon: Cpu },
  { label: 'Memory', value: 61, icon: Server },
  { label: 'Storage', value: 38, icon: HardDrive },
  { label: 'API load', value: 27, icon: Activity },
];

export default function AdminDashboardPage() {
  const statsQuery = useQuery({ queryKey: queryKeys.stats, queryFn: dashboardApi.stats });
  const jobsQuery = useQuery({ queryKey: queryKeys.jobs, queryFn: jobsApi.list });
  const interviewsQuery = useQuery({
    queryKey: queryKeys.interviews,
    queryFn: interviewsApi.list,
  });
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/api/health').then((r) => r.data),
    refetchInterval: 30_000,
  });

  const stats = statsQuery.data?.data;
  const health = healthQuery.data?.data;
  const jobs = jobsQuery.data?.data || [];
  const interviews = interviewsQuery.data?.data || [];

  const monthly = useMemo(
    () => (stats?.monthly_applications || []).map((m) => ({ name: m.month, value: m.count })),
    [stats]
  );

  if (statsQuery.isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Command center"
        subtitle="Platform analytics with live hiring metrics and demo infrastructure gauges."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ['Total jobs', stats?.total_jobs, BriefcaseIcon],
          ['Candidates', stats?.total_candidates, Users],
          ['Interviews', interviews.length, Activity],
          ['Active jobs', stats?.active_jobs, Database],
        ].map(([label, value, Icon]) => (
          <Card key={label} hover>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="mt-2 font-display text-3xl font-semibold">{value ?? 0}</p>
              </div>
              <div className="rounded-xl bg-[var(--sw-accent-soft)] p-2.5 text-accent">
                <Icon className="h-5 w-5" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Hiring velocity</CardTitle>
              <CardDescription>Applications over recent months</CardDescription>
            </div>
          </CardHeader>
          <AreaTrend data={monthly.length ? monthly : [{ name: '—', value: 0 }]} />
        </Card>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>AI & services</CardTitle>
              <CardDescription>Live health from backend</CardDescription>
            </div>
            <Badge variant={health?.ai?.ok ? 'success' : 'danger'}>
              {health?.ai?.ok ? 'Healthy' : 'Degraded'}
            </Badge>
          </CardHeader>
          <ul className="space-y-3 text-sm">
            <li className="flex justify-between">
              <span className="text-muted-foreground">Database</span>
              <span>{health?.database?.ok ? 'OK' : '—'}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-muted-foreground">AI service</span>
              <span>{health?.ai?.status || '—'}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-muted-foreground">NER model</span>
              <span>{String(health?.ai?.ner_model_loaded ?? '—')}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-muted-foreground">Embeddings</span>
              <span>{String(health?.ai?.embedding_model_loaded ?? '—')}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-muted-foreground">Vector backend</span>
              <span>{health?.ai?.vector_backend || '—'}</span>
            </li>
          </ul>
        </Card>
      </div>

      <div className="mt-6">
        <div className="mb-3 flex items-center gap-2">
          <CardTitle>Infrastructure</CardTitle>
          <Badge variant="warning">Demo gauges</Badge>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {DEMO_GAUGES.map((g) => (
            <Card key={g.label}>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-medium">{g.label}</p>
                <g.icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <p className="font-display text-2xl font-semibold">{g.value}%</p>
              <Progress className="mt-3" value={g.value} />
            </Card>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Job status mix</CardTitle>
          <div className="mt-4">
            <DonutChart
              data={[
                { name: 'Active', value: stats?.jobs_by_status?.active || 0 },
                { name: 'Closed', value: stats?.jobs_by_status?.closed || 0 },
                { name: 'Draft', value: stats?.jobs_by_status?.draft || 0 },
              ]}
            />
          </div>
        </Card>
        <Card>
          <CardTitle>Recent jobs</CardTitle>
          <div className="mt-4 space-y-2">
            {jobs.slice(0, 6).map((j) => (
              <div
                key={j.id}
                className="flex items-center justify-between rounded-xl border border-border px-3 py-2 text-sm"
              >
                <span className="font-medium">{j.title}</span>
                <Badge variant="secondary">{j.status}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function BriefcaseIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={props.className}>
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
    </svg>
  );
}

export function AdminHealthPage() {
  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get('/api/health').then((r) => r.data),
    refetchInterval: 15_000,
  });
  const health = healthQuery.data?.data;

  return (
    <div>
      <PageHeader title="System health" subtitle="Live probe of backend + AI service." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Service status</CardTitle>
          <pre className="mt-4 overflow-auto rounded-xl bg-muted/50 p-4 text-xs">
            {JSON.stringify(healthQuery.data || {}, null, 2)}
          </pre>
        </Card>
        <Card>
          <CardTitle>Usage trends (demo)</CardTitle>
          <div className="mt-4">
            <LinesChart
              data={[
                { name: 'Mon', api: 120, ai: 40 },
                { name: 'Tue', api: 160, ai: 55 },
                { name: 'Wed', api: 140, ai: 48 },
                { name: 'Thu', api: 190, ai: 70 },
                { name: 'Fri', api: 210, ai: 82 },
              ]}
              series={[
                { key: 'api', label: 'API calls', color: '#0d9488' },
                { key: 'ai', label: 'AI jobs', color: '#38bdf8' },
              ]}
            />
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Charts above are illustrative demo data. Live status uses{' '}
            <code>/api/health</code>
            {health?.ai?.ok ? ' — AI OK' : ''}.
          </p>
        </Card>
      </div>
    </div>
  );
}

export function AdminUsersPage() {
  const statsQuery = useQuery({ queryKey: queryKeys.stats, queryFn: dashboardApi.stats });
  return (
    <div>
      <PageHeader
        title="People overview"
        subtitle="Aggregate counts from hiring data (no user-admin API in backend)."
      />
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-muted-foreground">Candidates in system</p>
          <p className="mt-2 font-display text-4xl font-semibold">
            {statsQuery.data?.data?.total_candidates ?? '—'}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">Shortlisted</p>
          <p className="mt-2 font-display text-4xl font-semibold">
            {statsQuery.data?.data?.shortlisted ?? '—'}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted-foreground">Seed accounts</p>
          <p className="mt-2 text-sm text-muted-foreground">
            admin@cvscreening.local · hr@cvscreening.local
          </p>
          <Badge className="mt-3" variant="warning">
            Demo note
          </Badge>
        </Card>
      </div>
    </div>
  );
}
