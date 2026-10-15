import { useCallback, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  CheckCircle2,
  FileUp,
  Loader2,
  Sparkles,
  Upload,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { candidatesApi, jobsApi, queryKeys } from '../../api/endpoints';
import { getErrorMessage } from '../../api/client';
import { BarsChart, SkillRadar } from '../../components/charts/Charts';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardTitle } from '../../components/ui/card';
import { Modal } from '../../components/ui/modal';
import { TabsContent, TabsList, TabsRoot, TabsTrigger } from '../../components/ui/tabs';
import { UserAvatar } from '../../components/ui/avatar';
import { Progress, ScoreRing } from '../../components/ui/progress';
import { EmptyState, PageHeader, Skeleton, Spinner } from '../../components/ui/misc';
import { cn, scoreColor } from '../../lib/utils';

function CvDropzone({ onFiles, busy, progress }) {
  const onDrop = useCallback(
    (accepted) => {
      if (accepted?.length) onFiles(accepted);
    },
    [onFiles]
  );
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    disabled: busy,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        'relative cursor-pointer overflow-hidden rounded-3xl border-2 border-dashed px-6 py-14 text-center transition',
        isDragActive
          ? 'border-accent bg-[var(--sw-accent-soft)]'
          : 'border-border bg-muted/30 hover:border-accent/50',
        busy && 'pointer-events-none opacity-70'
      )}
    >
      <input {...getInputProps()} aria-label="Upload CV files" />
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--sw-accent-soft)] text-accent">
        {busy ? <Loader2 className="h-6 w-6 animate-spin" /> : <Upload className="h-6 w-6" />}
      </div>
      <p className="font-display text-xl font-semibold">
        {isDragActive ? 'Drop to upload' : 'Drag & drop CVs'}
      </p>
      <p className="mt-2 text-sm text-muted-foreground">
        PDF, DOCX, PNG, JPEG — single or bulk. AI extraction starts automatically.
      </p>
      {busy ? (
        <div className="mx-auto mt-6 max-w-sm space-y-2">
          <Progress value={progress} />
          <p className="text-xs text-muted-foreground">Processing pipeline… {progress}%</p>
        </div>
      ) : null}
    </div>
  );
}

function CandidateProfileModal({ candidateId, onClose }) {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.candidate(candidateId),
    queryFn: () => candidatesApi.get(candidateId),
    enabled: Boolean(candidateId),
  });
  const c = data?.data;

  return (
    <Modal
      open={Boolean(candidateId)}
      onOpenChange={(o) => !o && onClose()}
      title="Candidate profile"
      className="w-[min(92vw,720px)]"
    >
      {isLoading || !c ? (
        <Spinner />
      ) : (
        <div className="space-y-5">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-accent/30 via-sky-500/10 to-transparent p-5">
            <div className="flex items-center gap-4">
              <UserAvatar name={c.full_name || 'Candidate'} size="xl" />
              <div>
                <h3 className="font-display text-2xl font-semibold">{c.full_name || 'Unnamed'}</h3>
                <p className="text-sm text-muted-foreground">
                  {c.email || 'No email'} · {c.phone || 'No phone'}
                </p>
              </div>
            </div>
          </div>
          <TabsRoot defaultValue="overview">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="skills">Skills</TabsTrigger>
              <TabsTrigger value="experience">Experience</TabsTrigger>
              <TabsTrigger value="education">Education</TabsTrigger>
            </TabsList>
            <TabsContent value="overview" className="grid gap-3 sm:grid-cols-2">
              <Card className="!p-4">
                <p className="text-xs text-muted-foreground">Experience</p>
                <p className="font-display text-2xl font-semibold">{c.years_of_experience ?? '—'} yrs</p>
              </Card>
              <Card className="!p-4">
                <p className="text-xs text-muted-foreground">Communication</p>
                <p className="font-display text-2xl font-semibold">
                  {(Number(c.communication_score || 0) * 100).toFixed(0)}%
                </p>
              </Card>
            </TabsContent>
            <TabsContent value="skills">
              <div className="flex flex-wrap gap-2">
                {(c.technical_skills || []).length ? (
                  c.technical_skills.map((s) => (
                    <Badge key={s}>{s}</Badge>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">None extracted</p>
                )}
              </div>
            </TabsContent>
            <TabsContent value="experience">
              <ul className="space-y-2 text-sm">
                {(c.experience || []).length ? (
                  c.experience.map((e, i) => (
                    <li key={i} className="rounded-xl border border-border px-3 py-2">
                      {[e.job_title, e.company, e.duration].filter(Boolean).join(' · ') || 'Entry'}
                    </li>
                  ))
                ) : (
                  <li className="text-muted-foreground">None extracted</li>
                )}
              </ul>
            </TabsContent>
            <TabsContent value="education">
              <ul className="space-y-2 text-sm">
                {(c.education || []).length ? (
                  c.education.map((e, i) => (
                    <li key={i} className="rounded-xl border border-border px-3 py-2">
                      {[e.degree, e.university, e.graduation_year].filter(Boolean).join(' · ') || 'Entry'}
                    </li>
                  ))
                ) : (
                  <li className="text-muted-foreground">None extracted</li>
                )}
              </ul>
            </TabsContent>
          </TabsRoot>
        </div>
      )}
    </Modal>
  );
}

function criteriaFromRow(row) {
  const explanation = row.explanation || row.explanations || {};
  if (explanation.criteria && Object.keys(explanation.criteria).length) {
    return explanation.criteria;
  }
  const scores = Array.isArray(row.criterion_scores) ? row.criterion_scores : [];
  if (scores.length) {
    return Object.fromEntries(
      scores.map((c) => [c.criterion, Number(c.score ?? 0)])
    );
  }
  return {};
}

function rowScore(row) {
  const s = Number(row.overall_score ?? row.matching_percentage ?? row.score ?? 0);
  return s <= 1 ? s * 100 : s;
}

function rowKey(row, i) {
  return row.application_id || row.id || `${row.candidate_id}-${i}`;
}

const MAX_COMPARE = 3;

function CompareTable({ rows, onClear }) {
  const criteria = [...new Set(rows.flatMap(({ row }) => Object.keys(criteriaFromRow(row))))];
  const pct = (v) => Math.round(Number(v) <= 1 ? Number(v) * 100 : Number(v));
  return (
    <Card>
      <div className="flex items-center justify-between gap-3">
        <CardTitle>Side-by-side comparison</CardTitle>
        <Button variant="ghost" size="sm" onClick={onClear}>
          Clear
        </Button>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
              <th className="py-2 pr-4 font-semibold">Criterion</th>
              {rows.map(({ row, key }) => (
                <th key={key} className="py-2 pr-4 font-semibold">
                  {row.candidate_name || row.full_name || 'Unnamed Candidate'}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {criteria.map((c) => (
              <tr key={c} className="border-b border-border/60">
                <td className="py-2 pr-4 capitalize text-muted-foreground">{c.replace(/_/g, ' ')}</td>
                {rows.map(({ row, key }) => {
                  const v = criteriaFromRow(row)[c];
                  return (
                    <td key={key} className="py-2 pr-4">
                      {v == null ? '—' : `${pct(v)}%`}
                    </td>
                  );
                })}
              </tr>
            ))}
            <tr>
              <td className="py-2 pr-4 font-semibold">Overall match</td>
              {rows.map(({ row, key }) => (
                <td key={key} className="py-2 pr-4 font-semibold">
                  {Math.round(rowScore(row))}%
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function RankingCard({ row, onOpen, selected = false, onToggleCompare }) {
  const score = Number(row.overall_score ?? row.matching_percentage ?? row.score ?? 0);
  const normalized = score <= 1 ? score * 100 : score;
  const explanation = row.explanation || row.explanations || {};
  const criteria = criteriaFromRow(row);
  const radarData = Object.entries(criteria).map(([skill, v]) => ({
    skill: skill.replace(/_/g, ' '),
    score: Number(v) <= 1 ? Number(v) * 100 : Number(v),
  }));

  const strengths = explanation.strengths || explanation.pros || [];
  const weaknesses =
    explanation.gaps ||
    explanation.weaknesses ||
    explanation.missing_skills ||
    [];
  const displayName = row.candidate_name || row.full_name || 'Unnamed Candidate';

  return (
    <motion.div layout initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
      <Card hover className="h-full">
        <div className="flex items-start gap-4">
          <UserAvatar name={displayName} size="lg" />
          <div className="min-w-0 flex-1">
            <button
              type="button"
              className="text-left font-display text-lg font-semibold hover:text-accent"
              onClick={() => onOpen(row.candidate_id)}
            >
              {displayName}
            </button>
            <p className="text-xs text-muted-foreground">{row.email || '—'}</p>
            {row.shortlisted || row.is_shortlisted ? (
              <Badge variant="success" className="mt-2">
                Shortlisted
              </Badge>
            ) : null}
          </div>
          <ScoreRing score={normalized} label="Fit" />
        </div>

        {radarData.length ? (
          <div className="mt-4">
            <SkillRadar data={radarData.slice(0, 6)} />
          </div>
        ) : null}

        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Strengths
            </p>
            <ul className="space-y-1 text-sm">
              {(strengths.length ? strengths : ['Strong overall match']).slice(0, 3).map((s, i) => (
                <li key={i} className="flex gap-2 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>{typeof s === 'string' ? s : JSON.stringify(s)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Gaps
            </p>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {(weaknesses.length ? weaknesses : ['Review manually']).slice(0, 3).map((s, i) => (
                <li key={i}>• {typeof s === 'string' ? s : JSON.stringify(s)}</li>
              ))}
            </ul>
          </div>
        </div>

        {explanation.summary || explanation.rationale ? (
          <p className="mt-4 rounded-xl bg-muted/50 p-3 text-sm text-muted-foreground">
            {explanation.summary || explanation.rationale}
          </p>
        ) : null}

        <div className="mt-3 flex items-center justify-between gap-3">
          {onToggleCompare ? (
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={selected}
                onChange={onToggleCompare}
                className="rounded border-border"
              />
              Compare
            </label>
          ) : (
            <span />
          )}
          <p className={cn('font-display text-2xl font-semibold', scoreColor(normalized))}>
            {Math.round(normalized)}%
          </p>
        </div>
      </Card>
    </motion.div>
  );
}

export default function JobDetailPage({ basePath = '/hr' }) {
  const { jobId } = useParams();
  const qc = useQueryClient();
  const [tab, setTab] = useState('overview');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [minScore, setMinScore] = useState('');
  const [shortlistedOnly, setShortlistedOnly] = useState(false);
  const [compareKeys, setCompareKeys] = useState([]);

  const jobQuery = useQuery({
    queryKey: queryKeys.job(jobId),
    queryFn: () => jobsApi.get(jobId),
  });
  const candidatesQuery = useQuery({
    queryKey: queryKeys.candidates(jobId),
    queryFn: () => jobsApi.candidates(jobId),
  });
  const rankingsQuery = useQuery({
    queryKey: queryKeys.rankings(jobId),
    queryFn: () => jobsApi.rankings(jobId),
  });

  const uploadMutation = useMutation({
    mutationFn: async (files) => {
      setUploadProgress(12);
      const timer = setInterval(() => {
        setUploadProgress((p) => Math.min(88, p + 7));
      }, 400);
      try {
        if (files.length === 1) await jobsApi.uploadCv(jobId, files[0]);
        else await jobsApi.uploadBulk(jobId, files);
      } finally {
        clearInterval(timer);
        setUploadProgress(100);
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.candidates(jobId) });
      qc.invalidateQueries({ queryKey: queryKeys.stats });
      toast.success('CV processed & indexed');
      setTimeout(() => setUploadProgress(0), 800);
    },
    onError: (e) => {
      setUploadProgress(0);
      toast.error(getErrorMessage(e));
    },
  });

  const rankMutation = useMutation({
    mutationFn: () => jobsApi.rank(jobId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.rankings(jobId) });
      qc.invalidateQueries({ queryKey: queryKeys.candidates(jobId) });
      toast.success('AI ranking complete');
      setTab('rankings');
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const job = jobQuery.data?.data;
  const candidates = candidatesQuery.data?.data || [];
  const rankings = useMemo(() => {
    const raw = rankingsQuery.data?.data;
    if (Array.isArray(raw)) return raw;
    return raw?.results || raw?.rankings || [];
  }, [rankingsQuery.data]);

  const rankingChartData = useMemo(
    () =>
      [...rankings]
        .sort(
          (a, b) =>
            Number(b.matching_percentage ?? b.overall_score ?? 0) -
            Number(a.matching_percentage ?? a.overall_score ?? 0)
        )
        .map((row) => {
          const name = row.candidate_name || row.full_name || 'Unnamed Candidate';
          const score = Number(row.matching_percentage ?? row.overall_score ?? 0);
          return {
            name: name.length > 18 ? `${name.slice(0, 16)}…` : name,
            value: score <= 1 ? score * 100 : score,
          };
        }),
    [rankings]
  );

  const keyedRankings = useMemo(
    () => rankings.map((row, i) => ({ row, key: rowKey(row, i) })),
    [rankings]
  );
  const visibleRankings = useMemo(() => {
    const min = Number(minScore);
    return keyedRankings.filter(
      ({ row }) =>
        (!minScore || Number.isNaN(min) || rowScore(row) >= min) &&
        (!shortlistedOnly || row.shortlisted || row.is_shortlisted)
    );
  }, [keyedRankings, minScore, shortlistedOnly]);
  const compareRows = keyedRankings.filter(({ key }) => compareKeys.includes(key));

  function toggleCompare(key) {
    setCompareKeys((prev) => {
      if (prev.includes(key)) return prev.filter((k) => k !== key);
      if (prev.length >= MAX_COMPARE) {
        toast(`You can compare up to ${MAX_COMPARE} candidates`);
        return prev;
      }
      return [...prev, key];
    });
  }

  if (jobQuery.isLoading) return <Spinner label="Loading job…" />;
  if (!job) {
    return (
      <EmptyState
        title="Job not found"
        action={
          <Button asChild>
            <Link to={`${basePath}/jobs`}>Back to jobs</Link>
          </Button>
        }
      />
    );
  }

  return (
    <div>
      <Button variant="ghost" size="sm" className="mb-3" asChild>
        <Link to={`${basePath}/jobs`}>
          <ArrowLeft className="h-4 w-4" /> Jobs
        </Link>
      </Button>

      <PageHeader
        title={job.title}
        subtitle={`IT · ${job.status}`}
        actions={
          <>
            <Badge variant={job.status === 'active' ? 'success' : 'secondary'}>{job.status}</Badge>
            <Button
              onClick={() => rankMutation.mutate()}
              disabled={rankMutation.isPending || !candidates.length}
            >
              {rankMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Run AI ranking
            </Button>
          </>
        }
      />

      <TabsRoot value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="upload">Upload CVs</TabsTrigger>
          <TabsTrigger value="candidates">Candidates ({candidates.length})</TabsTrigger>
          <TabsTrigger value="rankings">AI Ranking ({rankings.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardTitle>Description</CardTitle>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                {job.description}
              </p>
            </Card>
            <Card>
              <CardTitle>Requirements</CardTitle>
              <div className="mt-3 space-y-3 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Skills</p>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {(job.required_skills || []).map((s) => (
                      <Badge key={s}>{s}</Badge>
                    ))}
                  </div>
                </div>
                <p>
                  <span className="text-muted-foreground">Experience:</span>{' '}
                  {job.minimum_experience ?? 0}+ years
                </p>
                <p>
                  <span className="text-muted-foreground">Education:</span>{' '}
                  {job.education_level || '—'}
                </p>
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="upload">
          <Card>
            <div className="mb-4 flex items-center gap-2 text-sm text-muted-foreground">
              <FileUp className="h-4 w-4 text-accent" />
              Upload → OCR/extract → index → ready to rank
            </div>
            <CvDropzone
              busy={uploadMutation.isPending}
              progress={uploadProgress}
              onFiles={(files) => uploadMutation.mutate(files)}
            />
            {uploadMutation.isSuccess ? (
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="mt-4 flex items-center gap-2 rounded-xl bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300"
              >
                <CheckCircle2 className="h-4 w-4" /> Extraction complete — candidates updated.
              </motion.div>
            ) : null}
          </Card>
        </TabsContent>

        <TabsContent value="candidates">
          {candidatesQuery.isLoading ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          ) : !candidates.length ? (
            <EmptyState title="No candidates" description="Upload CVs to populate this pipeline." />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {candidates.map((c) => (
                <button
                  key={c.id || c.candidate_id}
                  type="button"
                  onClick={() => setSelectedCandidate(c.candidate_id || c.id)}
                  className="glass rounded-2xl p-4 text-left transition hover:-translate-y-0.5"
                >
                  <div className="flex items-center gap-3">
                    <UserAvatar name={c.full_name || c.candidate_name || 'C'} />
                    <div>
                      <p className="font-semibold">{c.full_name || c.candidate_name}</p>
                      <p className="text-xs text-muted-foreground">{c.email}</p>
                    </div>
                  </div>
                  <Badge className="mt-3" variant="secondary">
                    {c.status || 'applied'}
                  </Badge>
                </button>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="rankings">
          {rankingsQuery.isLoading ? (
            <Spinner label="Loading rankings…" />
          ) : !rankings.length ? (
            <EmptyState
              icon={Sparkles}
              title="No rankings yet"
              description="Run AI ranking to generate explainable scores and shortlists."
              action={
                <Button onClick={() => rankMutation.mutate()} disabled={!candidates.length}>
                  <Sparkles className="h-4 w-4" /> Rank now
                </Button>
              }
            />
          ) : (
            <div className="space-y-4">
              {rankingChartData.length ? (
                <Card>
                  <CardTitle>Candidate match scores</CardTitle>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Ranked by actual AI matching percentage
                  </p>
                  <div className="mt-4">
                    <BarsChart data={rankingChartData} xKey="name" yKey="value" />
                  </div>
                </Card>
              ) : null}
              <Card className="!p-4">
                <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
                  <label className="flex items-center gap-2 text-muted-foreground">
                    Minimum score (%)
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={minScore}
                      onChange={(e) => setMinScore(e.target.value)}
                      placeholder="0"
                      aria-label="Minimum score percent"
                      className="w-20 rounded-lg border border-border bg-background/70 px-2 py-1 text-foreground"
                    />
                  </label>
                  <label className="flex items-center gap-2 text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={shortlistedOnly}
                      onChange={(e) => setShortlistedOnly(e.target.checked)}
                      className="rounded border-border"
                    />
                    Shortlisted only
                  </label>
                  <span className="text-muted-foreground">
                    Showing {visibleRankings.length} of {rankings.length} · tick “Compare” on up to{' '}
                    {MAX_COMPARE} candidates
                  </span>
                </div>
              </Card>
              {compareRows.length >= 2 ? (
                <CompareTable rows={compareRows} onClear={() => setCompareKeys([])} />
              ) : null}
              {!visibleRankings.length ? (
                <EmptyState
                  title="No candidates match the filters"
                  description="Lower the minimum score or untick “Shortlisted only”."
                />
              ) : (
                <div className="grid gap-4 lg:grid-cols-2">
                  {visibleRankings.map(({ row, key }) => (
                    <RankingCard
                      key={key}
                      row={row}
                      onOpen={setSelectedCandidate}
                      selected={compareKeys.includes(key)}
                      onToggleCompare={() => toggleCompare(key)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </TabsRoot>

      <CandidateProfileModal
        candidateId={selectedCandidate}
        onClose={() => setSelectedCandidate(null)}
      />
    </div>
  );
}
