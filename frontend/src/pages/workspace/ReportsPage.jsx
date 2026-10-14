import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, Printer } from 'lucide-react';
import { dashboardApi, jobsApi, queryKeys } from '../../api/endpoints';
import { AreaTrend, BarsChart, DonutChart } from '../../components/charts/Charts';
import { Button } from '../../components/ui/button';
import { Card, CardTitle } from '../../components/ui/card';
import { PageHeader, Spinner } from '../../components/ui/misc';
import { downloadCsv } from '../../lib/utils';

export default function ReportsPage() {
  const statsQuery = useQuery({ queryKey: queryKeys.stats, queryFn: dashboardApi.stats });
  const jobsQuery = useQuery({ queryKey: queryKeys.jobs, queryFn: jobsApi.list });
  const stats = statsQuery.data?.data;
  const jobs = jobsQuery.data?.data || [];

  const monthly = useMemo(
    () => (stats?.monthly_applications || []).map((m) => ({ name: m.month, value: m.count })),
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

  function exportJobsCsv() {
    downloadCsv('screenwise-jobs.csv', [
      ['Title', 'Industry', 'Status', 'Created'],
      ...jobs.map((j) => [j.title, j.industry, j.status, j.created_at]),
    ]);
  }

  if (statsQuery.isLoading) return <Spinner />;

  return (
    <div>
      <PageHeader
        title="Reports"
        subtitle="Interactive analytics with client-side export."
        actions={
          <>
            <Button variant="secondary" onClick={exportJobsCsv}>
              <Download className="h-4 w-4" /> CSV
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                window.print();
              }}
            >
              <Printer className="h-4 w-4" /> Print / PDF
            </Button>
          </>
        }
      />

      <div className="mb-4 grid gap-4 sm:grid-cols-4">
        {[
          ['Jobs', stats?.total_jobs],
          ['Candidates', stats?.total_candidates],
          ['Shortlisted', stats?.shortlisted],
          ['Active', stats?.active_jobs],
        ].map(([label, value]) => (
          <Card key={label} className="!p-4">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="font-display text-3xl font-semibold">{value ?? 0}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Applications over time</CardTitle>
          <div className="mt-4">
            <AreaTrend data={monthly.length ? monthly : [{ name: '—', value: 0 }]} />
          </div>
        </Card>
        <Card>
          <CardTitle>Jobs by status</CardTitle>
          <div className="mt-4">
            <DonutChart data={statusData} />
          </div>
        </Card>
        <Card className="lg:col-span-2">
          <CardTitle>IT job volume</CardTitle>
          <div className="mt-4">
            <BarsChart
              data={Object.entries(
                jobs.reduce((acc, j) => {
                  const k = j.industry || 'other';
                  acc[k] = (acc[k] || 0) + 1;
                  return acc;
                }, {})
              ).map(([name, value]) => ({ name, value }))}
            />
          </div>
        </Card>
      </div>
    </div>
  );
}
