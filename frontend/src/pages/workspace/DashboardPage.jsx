import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  ArrowUpRight,
  Briefcase,
  CalendarDays,
  Sparkles,
  Users,
} from 'lucide-react';
import { dashboardApi, interviewsApi, jobsApi, queryKeys } from '../../api/endpoints';
import { AreaTrend, BarsChart, DonutChart } from '../../components/charts/Charts';
import { Card, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { EmptyState, PageHeader, Skeleton } from '../../components/ui/misc';
import { formatDate } from '../../lib/utils';
import { FadeItem, Stagger } from '../../components/motion/PageTransition';

function Kpi({ label, value, icon: Icon, hint }) {
  return (
    <Card hover className="relative overflow-hidden">
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-accent/10 blur-2xl" />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-2 font-display text-3xl font-semibold">{value}</p>
          {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--sw-accent-soft)] text-accent">
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Card>
  );
}

export default function WorkspaceDashboard({ basePath = '/hr' }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.stats,
    queryFn: dashboardApi.stats,
  });
  const interviewsQuery = useQuery({
    queryKey: queryKeys.interviews,
    queryFn: interviewsApi.list,
  });
  const jobsQuery = useQuery({
    queryKey: queryKeys.jobs,
    queryFn: jobsApi.list,
  });

  const stats = data?.data;
  const interviews = interviewsQuery.data?.data || [];
  const jobs = jobsQuery.data?.data || [];

  const monthly = useMemo(
    () =>
      (stats?.monthly_applications || []).map((m) => ({
        name: m.month,
        value: m.count,
      })),
    [stats]
  );

  const statusData = useMemo(
    () =>
      stats
        ? [
            { name: 'Active', value: stats.jobs_by_status?.active || 0 },
            { name: 'Closed', value: stats.jobs_by_status?.closed || 0 },
            { name: 'Draft', value: stats.jobs_by_status?.draft || 0 },
          ]
        : [],
    [stats]
  );

  const upcoming = interviews
    .filter((i) => i.status !== 'cancelled' && new Date(i.scheduled_at) >= new Date())
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
    .slice(0, 5);

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <EmptyState
        title="Dashboard unavailable"
        description="Ensure the backend and MySQL are running, then refresh."
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Recruitment overview"
        subtitle="Pipeline health, AI ranking volume, and upcoming interviews."
        actions={
          <>
            <Button variant="secondary" asChild>
              <Link to={`${basePath}/search`}>AI Search</Link>
            </Button>
            <Button asChild>
              <Link to={`${basePath}/jobs`}>
                Manage jobs <ArrowUpRight className="h-4 w-4" />
              </Link>
            </Button>
          </>
        }
      />

      <Stagger className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <FadeItem>
          <Kpi label="Total jobs" value={stats.total_jobs} icon={Briefcase} />
        </FadeItem>
        <FadeItem>
          <Kpi label="Active roles" value={stats.active_jobs} icon={Sparkles} hint="Open pipelines" />
        </FadeItem>
        <FadeItem>
          <Kpi label="Candidates" value={stats.total_candidates} icon={Users} />
        </FadeItem>
        <FadeItem>
          <Kpi label="Shortlisted" value={stats.shortlisted} icon={CalendarDays} />
        </FadeItem>
      </Stagger>

      <div className="mt-6 grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <div>
              <CardTitle>Application trend</CardTitle>
              <CardDescription>Monthly CV intake across your vacancies</CardDescription>
            </div>
          </CardHeader>
          {monthly.length ? (
            <AreaTrend data={monthly} />
          ) : (
            <BarsChart data={[{ name: '—', value: 0 }]} />
          )}
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Job mix</CardTitle>
              <CardDescription>Active vs closed vs draft</CardDescription>
            </div>
          </CardHeader>
          <DonutChart data={statusData} />
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Upcoming interviews</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link to={`${basePath}/interviews`}>Calendar</Link>
            </Button>
          </CardHeader>
          <div className="space-y-3">
            {upcoming.length ? (
              upcoming.map((iv) => (
                <motion.div
                  key={iv.id}
                  layout
                  className="flex items-center justify-between rounded-xl border border-border bg-background/40 px-3 py-3"
                >
                  <div>
                    <p className="text-sm font-semibold">{iv.candidate_name || 'Candidate'}</p>
                    <p className="text-xs text-muted-foreground">{iv.job_title || 'Role'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium">{formatDate(iv.scheduled_at)}</p>
                    <Badge className="mt-1">{iv.mode}</Badge>
                  </div>
                </motion.div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No upcoming interviews scheduled.</p>
            )}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active jobs</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link to={`${basePath}/jobs`}>View all</Link>
            </Button>
          </CardHeader>
          <div className="space-y-3">
            {jobs
              .filter((j) => j.status === 'active')
              .slice(0, 5)
              .map((j) => (
                <Link
                  key={j.id}
                  to={`${basePath}/jobs/${j.id}`}
                  className="flex items-center justify-between rounded-xl border border-border bg-background/40 px-3 py-3 transition hover:border-accent/40"
                >
                  <div>
                    <p className="text-sm font-semibold">{j.title}</p>
                    <p className="text-xs capitalize text-muted-foreground">{j.industry}</p>
                  </div>
                  <Badge variant="success">{j.status}</Badge>
                </Link>
              ))}
            {!jobs.filter((j) => j.status === 'active').length ? (
              <p className="text-sm text-muted-foreground">Create a job to start screening.</p>
            ) : null}
          </div>
        </Card>
      </div>
    </div>
  );
}
