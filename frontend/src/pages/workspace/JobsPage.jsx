import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { LayoutGrid, List, Columns3, Plus, Search } from 'lucide-react';
import toast from 'react-hot-toast';
import { jobsApi, rankingApi, queryKeys } from '../../api/endpoints';
import { getErrorMessage } from '../../api/client';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Input, Textarea } from '../../components/ui/input';
import { Select } from '../../components/ui/select';
import { Modal } from '../../components/ui/modal';
import { EmptyState, PageHeader, Skeleton } from '../../components/ui/misc';
import { cn } from '../../lib/utils';

const INDUSTRIES = ['it'];

function statusVariant(status) {
  if (status === 'active') return 'success';
  if (status === 'closed') return 'danger';
  return 'warning';
}

function JobForm({ initial, onSubmit, submitting }) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: {
      title: initial?.title || '',
      description: initial?.description || '',
      requiredSkills: (initial?.required_skills || []).join(', '),
      minimumExperience: initial?.minimum_experience ?? 0,
      educationLevel: initial?.education_level || '',
      industry: initial?.industry || 'it',
      requiredCertifications: (initial?.required_certifications || []).join(', '),
      status: initial?.status || 'active',
    },
  });
  const industry = watch('industry');
  const { data: weightsData } = useQuery({
    queryKey: queryKeys.weights(industry),
    queryFn: () => rankingApi.weights(industry),
  });

  return (
    <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
      <Input label="Job title" error={errors.title?.message} {...register('title', { required: 'Required' })} />
      <Textarea label="Description" error={errors.description?.message} {...register('description', { required: 'Required' })} />
      <Input label="Required skills (comma-separated)" {...register('requiredSkills')} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Min experience (years)" type="number" step="0.5" min="0" {...register('minimumExperience', { valueAsNumber: true })} />
        <Input label="Education level" {...register('educationLevel')} />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Select label="Industry" {...register('industry')}>
          {INDUSTRIES.map((i) => (
            <option key={i} value={i}>{i}</option>
          ))}
        </Select>
        <Select label="Status" {...register('status')}>
          <option value="active">active</option>
          <option value="draft">draft</option>
          <option value="closed">closed</option>
        </Select>
      </div>
      <Input label="Certifications (comma-separated)" {...register('requiredCertifications')} />
      {weightsData?.data?.weights ? (
        <div className="rounded-xl border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
          Ranking weights ({industry}):{' '}
          {Object.entries(weightsData.data.weights)
            .map(([k, v]) => `${k} ${(Number(v) * 100).toFixed(0)}%`)
            .join(' · ')}
        </div>
      ) : null}
      <Button type="submit" className="w-full" disabled={submitting}>
        {submitting ? 'Saving…' : 'Save job'}
      </Button>
    </form>
  );
}

export default function JobsPage({ basePath = '/hr' }) {
  const qc = useQueryClient();
  const [view, setView] = useState('grid');
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const { data, isLoading } = useQuery({ queryKey: queryKeys.jobs, queryFn: jobsApi.list });
  const jobs = data?.data || [];

  const filtered = useMemo(() => {
    return jobs.filter((j) => {
      const matchQ =
        !q ||
        j.title?.toLowerCase().includes(q.toLowerCase()) ||
        j.industry?.toLowerCase().includes(q.toLowerCase());
      const matchS = statusFilter === 'all' || j.status === statusFilter;
      return matchQ && matchS;
    });
  }, [jobs, q, statusFilter]);

  const createMutation = useMutation({
    mutationFn: (payload) =>
      editing ? jobsApi.update(editing.id, payload) : jobsApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.jobs });
      toast.success(editing ? 'Job updated' : 'Job created');
      setModalOpen(false);
      setEditing(null);
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const actionMutation = useMutation({
    mutationFn: ({ id, action }) => {
      if (action === 'close') return jobsApi.close(id);
      if (action === 'duplicate') return jobsApi.duplicate(id);
      if (action === 'delete') return jobsApi.remove(id);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.jobs });
      toast.success('Done');
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  function mapForm(values) {
    return {
      title: values.title,
      description: values.description,
      requiredSkills: String(values.requiredSkills || '')
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      minimumExperience: Number(values.minimumExperience) || 0,
      educationLevel: values.educationLevel,
      industry: values.industry,
      requiredCertifications: String(values.requiredCertifications || '')
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      status: values.status,
    };
  }

  const columns = {
    draft: filtered.filter((j) => j.status === 'draft'),
    active: filtered.filter((j) => j.status === 'active'),
    closed: filtered.filter((j) => j.status === 'closed'),
  };

  return (
    <div>
      <PageHeader
        title="Jobs"
        subtitle="Create vacancies, track pipeline status, and open ranking workspaces."
        actions={
          <Button
            onClick={() => {
              setEditing(null);
              setModalOpen(true);
            }}
          >
            <Plus className="h-4 w-4" /> New job
          </Button>
        }
      />

      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-md flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search jobs…"
            className="h-11 w-full rounded-xl border border-border bg-background/60 pl-10 pr-3 text-sm"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select
            className="w-36"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All status</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="closed">Closed</option>
          </Select>
          <div className="inline-flex rounded-xl border border-border bg-muted/40 p-1">
            {[
              { id: 'grid', icon: LayoutGrid },
              { id: 'list', icon: List },
              { id: 'kanban', icon: Columns3 },
            ].map((v) => (
              <button
                key={v.id}
                type="button"
                onClick={() => setView(v.id)}
                className={cn(
                  'rounded-lg p-2 text-muted-foreground',
                  view === v.id && 'bg-card text-accent shadow-sm'
                )}
                aria-label={v.id}
              >
                <v.icon className="h-4 w-4" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : !filtered.length ? (
        <EmptyState
          title="No jobs yet"
          description="Create your first vacancy to start uploading CVs."
          action={
            <Button onClick={() => setModalOpen(true)}>
              <Plus className="h-4 w-4" /> Create job
            </Button>
          }
        />
      ) : view === 'kanban' ? (
        <div className="grid gap-4 lg:grid-cols-3">
          {Object.entries(columns).map(([status, items]) => (
            <div key={status} className="rounded-2xl border border-border bg-muted/30 p-3">
              <div className="mb-3 flex items-center justify-between px-1">
                <p className="text-sm font-semibold capitalize">{status}</p>
                <Badge variant="secondary">{items.length}</Badge>
              </div>
              <div className="space-y-3">
                {items.map((j) => (
                  <Card key={j.id} hover className="!p-4">
                    <Link to={`${basePath}/jobs/${j.id}`} className="font-semibold hover:text-accent">
                      {j.title}
                    </Link>
                    <p className="mt-1 text-xs capitalize text-muted-foreground">{j.industry}</p>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : view === 'list' ? (
        <div className="overflow-hidden rounded-2xl border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Industry</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((j) => (
                <tr key={j.id} className="border-t border-border">
                  <td className="px-4 py-3">
                    <Link to={`${basePath}/jobs/${j.id}`} className="font-semibold hover:text-accent">
                      {j.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 capitalize text-muted-foreground">{j.industry}</td>
                  <td className="px-4 py-3">
                    <Badge variant={statusVariant(j.status)}>{j.status}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      <Button size="sm" variant="ghost" onClick={() => { setEditing(j); setModalOpen(true); }}>
                        Edit
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => actionMutation.mutate({ id: j.id, action: 'duplicate' })}>
                        Duplicate
                      </Button>
                      {j.status !== 'closed' ? (
                        <Button size="sm" variant="ghost" onClick={() => actionMutation.mutate({ id: j.id, action: 'close' })}>
                          Close
                        </Button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((j) => (
            <Card key={j.id} hover>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <Link to={`${basePath}/jobs/${j.id}`} className="font-display text-lg font-semibold hover:text-accent">
                    {j.title}
                  </Link>
                  <p className="mt-1 text-xs capitalize text-muted-foreground">{j.industry}</p>
                </div>
                <Badge variant={statusVariant(j.status)}>{j.status}</Badge>
              </div>
              <p className="mt-3 line-clamp-3 text-sm text-muted-foreground">{j.description}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button size="sm" asChild>
                  <Link to={`${basePath}/jobs/${j.id}`}>Open</Link>
                </Button>
                <Button size="sm" variant="secondary" onClick={() => { setEditing(j); setModalOpen(true); }}>
                  Edit
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        onOpenChange={setModalOpen}
        title={editing ? 'Edit job' : 'Create job'}
        description="Vacancies feed AI ranking weights by industry."
      >
        <JobForm
          initial={editing}
          submitting={createMutation.isPending}
          onSubmit={(values) => createMutation.mutate(mapForm(values))}
        />
      </Modal>
    </div>
  );
}
