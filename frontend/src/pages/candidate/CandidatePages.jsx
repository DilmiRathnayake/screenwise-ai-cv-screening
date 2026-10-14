import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import { Award, Briefcase, Loader2, Sparkles } from 'lucide-react';
import { candidatePortalApi, queryKeys } from '../../api/endpoints';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardTitle } from '../../components/ui/card';
import { Progress, ScoreRing } from '../../components/ui/progress';
import { UserAvatar } from '../../components/ui/avatar';
import { PageHeader } from '../../components/ui/misc';
import { EmptyState } from '../../components/ui/misc';
import { formatDate } from '../../lib/utils';

function LoadingCard() {
  return (
    <div className="flex items-center justify-center py-16 text-muted-foreground">
      <Loader2 className="h-6 w-6 animate-spin" />
    </div>
  );
}

export function CandidateHomePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.candidateDashboard,
    queryFn: candidatePortalApi.dashboard,
  });

  if (isLoading) return <LoadingCard />;
  if (isError) {
    return (
      <EmptyState
        title="Could not load dashboard"
        description="Sign in again or check that the backend is running."
      />
    );
  }

  const payload = data?.data || {};
  const { profile = {}, applications = [], recommended = [], achievements = [], feedback = [] } =
    payload;

  return (
    <div>
      <PageHeader
        title={`Welcome, ${(profile.name || 'Candidate').split(' ')[0]}`}
        subtitle="Track applications, interviews, and AI resume feedback."
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2 overflow-hidden !p-0">
          <div className="bg-gradient-to-r from-accent/25 via-sky-500/10 to-transparent p-6">
            <div className="flex items-center gap-4">
              <UserAvatar name={profile.name} size="xl" />
              <div>
                <h2 className="font-display text-2xl font-semibold">{profile.name}</h2>
                <p className="text-sm text-muted-foreground">
                  {profile.title} · {profile.location}
                </p>
              </div>
            </div>
            <div className="mt-6">
              <div className="mb-2 flex justify-between text-sm">
                <span>Profile completion</span>
                <span className="font-semibold">{profile.completion}%</span>
              </div>
              <Progress value={profile.completion} />
            </div>
          </div>
        </Card>
        <Card className="flex flex-col items-center justify-center">
          <ScoreRing score={profile.resumeScore} label="Resume" size={110} />
          <p className="mt-3 text-sm text-muted-foreground">AI resume score</p>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle>Application progress</CardTitle>
          <div className="mt-4 space-y-4">
            {!applications.length ? (
              <p className="text-sm text-muted-foreground">
                No applications yet. When HR uploads your CV to a job, it appears here.
              </p>
            ) : (
              applications.map((a) => (
                <div key={a.id}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="font-medium">{a.role}</span>
                    <Badge>{a.status}</Badge>
                  </div>
                  <p className="mb-2 text-xs text-muted-foreground">{a.company}</p>
                  <Progress value={a.progress} />
                </div>
              ))
            )}
          </div>
        </Card>
        <Card>
          <CardTitle>AI feedback</CardTitle>
          <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
            {feedback.map((f) => (
              <li key={f} className="flex gap-2">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                {f}
              </li>
            ))}
          </ul>
          <CardTitle className="mt-6">Achievements</CardTitle>
          <div className="mt-3 flex flex-wrap gap-2">
            {achievements.length ? (
              achievements.map((a) => (
                <Badge key={a} variant="success">
                  <Award className="mr-1 h-3 w-3" /> {a}
                </Badge>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">Complete your profile to unlock badges.</p>
            )}
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <div className="mb-4 flex items-center justify-between">
          <CardTitle>Recommended jobs</CardTitle>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/candidate/applications">View pipeline</Link>
          </Button>
        </div>
        {!recommended.length ? (
          <p className="text-sm text-muted-foreground">
            No open roles to recommend right now, or you have already applied to all active jobs.
          </p>
        ) : (
          <div className="grid gap-3 md:grid-cols-3">
            {recommended.map((r, i) => (
              <motion.div
                key={r.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="rounded-2xl border border-border bg-background/50 p-4"
              >
                <p className="font-semibold">{r.title}</p>
                <p className="text-xs text-muted-foreground">{r.company}</p>
                <p className="mt-3 font-display text-2xl text-accent">{r.match}%</p>
              </motion.div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export function CandidateApplicationsPage() {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.candidateApplications,
    queryFn: candidatePortalApi.applications,
  });
  const applications = data?.data || [];

  return (
    <div>
      <PageHeader title="Applications" subtitle="Your live application pipeline." />
      {isLoading ? (
        <LoadingCard />
      ) : !applications.length ? (
        <EmptyState
          title="No applications yet"
          description="Applications appear when your CV is uploaded and linked to your account email."
        />
      ) : (
        <div className="space-y-3">
          {applications.map((a) => (
            <Card key={a.id} className="!p-4">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-[var(--sw-accent-soft)] p-2 text-accent">
                  <Briefcase className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold">{a.role}</p>
                  <p className="text-xs text-muted-foreground">{a.company}</p>
                </div>
                <Badge>{a.status}</Badge>
              </div>
              <Progress className="mt-3" value={a.progress} />
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export function CandidateCalendarPage() {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.candidateInterviews,
    queryFn: candidatePortalApi.interviews,
  });
  const interviews = data?.data || [];
  const events = interviews.map((i) => ({
    id: i.id,
    title: i.title,
    start: i.start,
  }));

  return (
    <div>
      <PageHeader title="Interview schedule" subtitle="Interviews scheduled by recruiters." />
      <Card>
        {isLoading ? (
          <LoadingCard />
        ) : (
          <FullCalendar
            plugins={[dayGridPlugin, timeGridPlugin, listPlugin]}
            initialView="listWeek"
            height="auto"
            events={events}
            headerToolbar={{ left: 'prev,next', center: 'title', right: 'dayGridMonth,listWeek' }}
          />
        )}
      </Card>
      <div className="mt-4 space-y-2">
        {!interviews.length && !isLoading ? (
          <p className="text-sm text-muted-foreground">No interviews scheduled yet.</p>
        ) : (
          interviews.map((i) => (
            <Card key={i.id} className="!p-4 text-sm">
              <p className="font-semibold">{i.title}</p>
              <p className="text-muted-foreground">{formatDate(i.start)}</p>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

export function CandidateProfilePage() {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.candidateProfile,
    queryFn: candidatePortalApi.profile,
  });
  const p = data?.data?.profile;

  if (isLoading) return <LoadingCard />;
  if (!p) {
    return (
      <EmptyState title="Profile unavailable" description="Could not load your candidate profile." />
    );
  }

  return (
    <div>
      <PageHeader title="Profile" subtitle="Your profile from CV extraction and account details." />
      <Card className="overflow-hidden !p-0">
        <div className="h-32 bg-gradient-to-r from-accent/40 via-sky-500/20 to-transparent" />
        <div className="-mt-10 px-6 pb-6">
          <UserAvatar name={p.name} size="xl" className="ring-4 ring-background" />
          <h2 className="mt-3 font-display text-2xl font-semibold">{p.name}</h2>
          <p className="text-muted-foreground">{p.title}</p>
          <p className="mt-1 text-sm text-muted-foreground">{p.email}</p>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <Card className="!p-4">
              <p className="text-xs text-muted-foreground">Completion</p>
              <p className="font-display text-2xl">{p.completion}%</p>
            </Card>
            <Card className="!p-4">
              <p className="text-xs text-muted-foreground">Resume score</p>
              <p className="font-display text-2xl">{p.resumeScore}</p>
            </Card>
            <Card className="!p-4">
              <p className="text-xs text-muted-foreground">Location</p>
              <p className="font-display text-lg">{p.location}</p>
            </Card>
          </div>
        </div>
      </Card>
    </div>
  );
}
