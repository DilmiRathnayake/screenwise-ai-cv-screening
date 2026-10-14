import { useEffect, useMemo, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import toast from 'react-hot-toast';
import { CalendarPlus, Link2 } from 'lucide-react';
import { interviewsApi, jobsApi, queryKeys } from '../../api/endpoints';
import { getErrorMessage } from '../../api/client';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Input, Textarea } from '../../components/ui/input';
import { Select } from '../../components/ui/select';
import { Modal } from '../../components/ui/modal';
import { Badge } from '../../components/ui/badge';
import { EmptyState, PageHeader, Spinner } from '../../components/ui/misc';
import { formatDate } from '../../lib/utils';

const STATUS_COLOR = {
  scheduled: '#0d9488',
  rescheduled: '#38bdf8',
  completed: '#64748b',
  cancelled: '#f43f5e',
  no_show: '#f59e0b',
};

export default function InterviewsPage() {
  const qc = useQueryClient();
  const calendarRef = useRef(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState('');

  const interviewsQuery = useQuery({
    queryKey: queryKeys.interviews,
    queryFn: interviewsApi.list,
  });
  const jobsQuery = useQuery({ queryKey: queryKeys.jobs, queryFn: jobsApi.list });
  const candidatesQuery = useQuery({
    queryKey: queryKeys.candidates(selectedJobId),
    queryFn: () => jobsApi.candidates(selectedJobId),
    enabled: Boolean(selectedJobId),
  });

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { isSubmitting },
  } = useForm({
    defaultValues: { mode: 'online', durationMinutes: 45, jobId: '' },
  });

  const jobIdWatch = watch('jobId');
  useEffect(() => {
    setSelectedJobId(jobIdWatch || '');
  }, [jobIdWatch]);

  const scheduleMutation = useMutation({
    mutationFn: interviewsApi.schedule,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.interviews });
      toast.success('Interview scheduled');
      setModalOpen(false);
      reset({ mode: 'online', durationMinutes: 45 });
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const rescheduleMutation = useMutation({
    mutationFn: ({ id, scheduledAt }) =>
      interviewsApi.reschedule(id, { scheduledAt }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.interviews });
      toast.success('Rescheduled');
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const cancelMutation = useMutation({
    mutationFn: interviewsApi.cancel,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.interviews });
      toast.success('Cancelled');
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const interviews = interviewsQuery.data?.data || [];
  const jobs = jobsQuery.data?.data || [];
  const candidates = candidatesQuery.data?.data || [];

  const events = useMemo(
    () =>
      interviews
        .filter((i) => i.status !== 'cancelled')
        .map((i) => ({
          id: i.id,
          title: `${i.candidate_name || 'Candidate'} · ${i.job_title || 'Role'}`,
          start: i.scheduled_at,
          backgroundColor: STATUS_COLOR[i.status] || STATUS_COLOR.scheduled,
          borderColor: 'transparent',
          extendedProps: i,
        })),
    [interviews]
  );

  if (interviewsQuery.isLoading) return <Spinner label="Loading calendar…" />;

  return (
    <div>
      <PageHeader
        title="Interview calendar"
        subtitle="Day, week, month, and agenda views — drag to reschedule."
        actions={
          <>
            <Button
              variant="secondary"
              onClick={() =>
                toast('Demo — Google Calendar sync is configured via n8n webhook', {
                  icon: '📅',
                })
              }
            >
              <Link2 className="h-4 w-4" /> Google sync
            </Button>
            <Button onClick={() => setModalOpen(true)}>
              <CalendarPlus className="h-4 w-4" /> Schedule
            </Button>
          </>
        }
      />

      <Card className="overflow-hidden">
        <FullCalendar
          ref={calendarRef}
          plugins={[dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
          }}
          height="auto"
          editable
          droppable={false}
          events={events}
          eventDrop={(info) => {
            rescheduleMutation.mutate({
              id: info.event.id,
              scheduledAt: info.event.start.toISOString(),
            });
          }}
          eventClick={(info) => {
            const iv = info.event.extendedProps;
            const ok = window.confirm(
              `Cancel interview with ${iv.candidate_name || 'candidate'} on ${formatDate(iv.scheduled_at)}?`
            );
            if (ok) cancelMutation.mutate(iv.id);
          }}
        />
      </Card>

      <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {interviews.slice(0, 6).map((iv) => (
          <Card key={iv.id} className="!p-4">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-semibold">{iv.candidate_name || 'Candidate'}</p>
                <p className="text-xs text-muted-foreground">{iv.job_title}</p>
              </div>
              <Badge>{iv.status}</Badge>
            </div>
            <p className="mt-3 text-sm text-muted-foreground">{formatDate(iv.scheduled_at)}</p>
          </Card>
        ))}
        {!interviews.length ? (
          <EmptyState
            className="md:col-span-2 xl:col-span-3"
            title="No interviews"
            description="Schedule from shortlisted applications."
          />
        ) : null}
      </div>

      <Modal
        open={modalOpen}
        onOpenChange={setModalOpen}
        title="Schedule interview"
        description="Creates an interview record and optional n8n notification."
      >
        <form
          className="space-y-4"
          onSubmit={handleSubmit((values) => {
            scheduleMutation.mutate({
              applicationId: values.applicationId,
              scheduledAt: new Date(values.scheduledAt).toISOString(),
              durationMinutes: Number(values.durationMinutes) || 45,
              mode: values.mode,
              meetingLink: values.meetingLink,
              location: values.location,
              notes: values.notes,
            });
          })}
        >
          <Select label="Job" {...register('jobId', { required: true })}>
            <option value="">Select job</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title}
              </option>
            ))}
          </Select>
          <Select label="Application / candidate" {...register('applicationId', { required: true })}>
            <option value="">Select candidate</option>
            {candidates.map((c) => (
              <option key={c.application_id || c.id} value={c.application_id || c.id}>
                {c.full_name || c.candidate_name || c.email}
              </option>
            ))}
          </Select>
          <Input
            label="Scheduled at"
            type="datetime-local"
            {...register('scheduledAt', { required: true })}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Duration (minutes)"
              type="number"
              {...register('durationMinutes', { valueAsNumber: true })}
            />
            <Select label="Mode" {...register('mode')}>
              <option value="online">online</option>
              <option value="onsite">onsite</option>
              <option value="phone">phone</option>
            </Select>
          </div>
          <Input label="Meeting link" {...register('meetingLink')} />
          <Input label="Location" {...register('location')} />
          <Textarea label="Notes" {...register('notes')} />
          <Button type="submit" className="w-full" disabled={isSubmitting || scheduleMutation.isPending}>
            Schedule
          </Button>
        </form>
      </Modal>
    </div>
  );
}
