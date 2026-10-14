import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Brain,
  Calendar,
  Check,
  ChevronDown,
  Search,
  Shield,
  Sparkles,
  Users,
} from 'lucide-react';
import { rankingApi, queryKeys } from '../../api/endpoints';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';

const features = [
  {
    icon: Brain,
    title: 'Explainable AI ranking',
    body: 'Industry-weighted scores with criterion breakdowns recruiters can defend.',
  },
  {
    icon: Search,
    title: 'Semantic talent search',
    body: 'Find candidates by intent - not brittle keyword filters.',
  },
  {
    icon: Calendar,
    title: 'Interview orchestration',
    body: 'Schedule, reschedule, and sync workflows without leaving the console.',
  },
  {
    icon: Shield,
    title: 'Enterprise-ready access',
    body: 'Role portals for Admin and HR with JWT-secured operations.',
  },
];

const STATIC_STATS = [
  { label: 'Faster shortlists', value: '10×' },
  { label: 'Formats supported', value: 'PDF/DOCX' },
  { label: 'Industries', value: 'IT' },
];

const faqs = [
  {
    q: 'Does ScreenWise replace human judgment?',
    a: 'No - it accelerates screening with transparent scores so HR can decide faster.',
  },
  {
    q: 'Which roles can sign in?',
    a: 'All three portals — Admin, HR, and Candidate — use the live API with role-based access.',
  },
  {
    q: 'Can we deploy on-prem for a viva demo?',
    a: 'Yes - Docker Compose ships the full stack for one-machine demos.',
  },
];

function formatPct(fraction) {
  if (fraction == null || Number.isNaN(fraction)) return '—';
  return `${Math.round(fraction * 1000) / 10}%`;
}

export default function LandingPage() {
  const [openFaq, setOpenFaq] = useState(0);
  const metricsQuery = useQuery({
    queryKey: queryKeys.model2Metrics,
    queryFn: rankingApi.model2Metrics,
    staleTime: 60_000,
  });
  const model2 = metricsQuery.data?.data;

  const stats = useMemo(() => {
    const top1 =
      model2?.top1_accuracy_pct ??
      (model2?.ml_model?.top1_accuracy != null
        ? model2.ml_model.top1_accuracy * 100
        : null);
    const rankingStat = {
      label: 'Model 2 accuracy',
      value: model2?.available && top1 != null ? `${Math.round(top1 * 10) / 10}%` : '—',
    };
    return [STATIC_STATS[0], rankingStat, ...STATIC_STATS.slice(1)];
  }, [model2]);

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 mesh-bg opacity-80" />
      <motion.div
        className="pointer-events-none absolute -left-24 top-24 h-72 w-72 rounded-full bg-accent/30 blur-3xl"
        animate={{ y: [0, 30, 0], x: [0, 20, 0] }}
        transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="pointer-events-none absolute right-0 top-40 h-80 w-80 rounded-full bg-sky-400/20 blur-3xl"
        animate={{ y: [0, -40, 0] }}
        transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
      />

      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-white">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="font-display text-xl font-semibold">ScreenWise</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" asChild>
            <Link to="/login">Sign in</Link>
          </Button>
          <Button asChild>
            <Link to="/login">
              Get started <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </header>

      <section className="relative z-10 mx-auto grid max-w-6xl gap-10 px-4 pb-20 pt-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:pt-16">
        <div>
          <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-accent">
            AI recruitment OS
          </p>
          <h1 className="font-display text-5xl font-semibold leading-[1.05] tracking-tight md:text-6xl">
            ScreenWise
          </h1>
          <p className="mt-4 max-w-xl text-lg text-muted-foreground">
            Rank talent with clarity. Extract, score, and shortlist candidates across industries -
            with a console that feels like Linear meets Greenhouse.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button size="lg" asChild>
              <Link to="/login/hr">
                Enter HR workspace <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="secondary" asChild>
              <Link to="/login">Choose portal</Link>
            </Button>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass relative overflow-hidden rounded-3xl p-6"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-accent/10 via-transparent to-sky-400/10" />
          <div className="relative space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold">Live ranking preview</p>
              <span className="rounded-full bg-[var(--sw-accent-soft)] px-2 py-0.5 text-xs text-accent">
                AI
              </span>
            </div>
            {['Dilmi Rathnayake · 92', 'Dil Thashmila · 87', 'Thashmila Rathnayake · 81'].map((row, i) => (
              <motion.div
                key={row}
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.25 + i * 0.1 }}
                className="flex items-center justify-between rounded-2xl border border-border bg-background/50 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-xs font-bold">
                    {row[0]}
                  </div>
                  <span className="text-sm font-medium">{row.split(' · ')[0]}</span>
                </div>
                <span className="font-display text-lg text-accent">{row.split(' · ')[1]}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      <section className="relative z-10 border-y border-border bg-card/40 py-10 backdrop-blur">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-4 md:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <p className="font-display text-3xl font-semibold text-gradient">{s.value}</p>
              <p className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">{s.label}</p>
            </div>
          ))}
        </div>
        <p className="mx-auto mt-4 max-w-6xl px-4 text-center text-[11px] text-muted-foreground">
          {model2?.available
            ? `Model 2 held-out test (${model2.test_jobs} jobs): top-1 accuracy ${model2.top1_accuracy_pct ?? formatPct(model2.ml_model?.top1_accuracy)} · NDCG@5 ${formatPct(model2.ml_model?.ndcg_at_5)}.`
            : 'Model 2 metrics load from evaluation/model2_metrics.json when the AI service is running.'}
        </p>
      </section>

      <section className="relative z-10 mx-auto max-w-6xl px-4 py-20">
        <h2 className="font-display text-3xl font-semibold">Built for modern talent teams</h2>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Every surface is designed for speed, clarity, and explainability — not another CRUD admin theme.
        </p>
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
            >
              <Card hover className="h-full">
                <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--sw-accent-soft)] text-accent">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="font-display text-xl font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.body}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-6xl px-4 pb-16">
        <p className="mb-6 text-center text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Trusted by modern hiring stacks
        </p>
        <div className="flex flex-wrap items-center justify-center gap-8 opacity-60">
          {['Infinit', 'Virtuza', 'Sysco Labs', 'Codegen', 'Vario Systems'].map((c) => (
            <span key={c} className="font-display text-lg font-semibold">
              {c}
            </span>
          ))}
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-6xl px-4 pb-20">
        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              quote: 'Shortlisting used to take days. ScreenWise made the why behind every score obvious.',
              name: 'Priya Peris.',
              role: 'Head of Talent',
            },
            {
              quote: 'The ranking explanations are dissertation-grade and still usable in daily hiring.',
              name: 'Namdini Perera.',
              role: 'HR Manager',
            },
            {
              quote: 'Feels like a product we could sell — not a student CRUD demo.',
              name: 'Dilmi Rathnayake.',
              role: 'People Ops',
            },
          ].map((t) => (
            <Card key={t.name} className="h-full">
              <p className="text-sm leading-relaxed text-foreground/90">“{t.quote}”</p>
              <div className="mt-4 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-muted text-xs font-bold">
                  {t.name[0]}
                </div>
                <div>
                  <p className="text-sm font-semibold">{t.name}</p>
                  <p className="text-xs text-muted-foreground">{t.role}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-6xl px-4 pb-20">
        <h2 className="font-display text-3xl font-semibold">Simple plans for demos</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            { name: 'Research', price: 'Free', items: ['Local Docker', 'HR workspace', 'AI ranking'] },
            {
              name: 'Team',
              price: 'Demo',
              items: ['Semantic search', 'Interview calendar', 'Notifications'],
              highlight: true,
            },
            { name: 'Enterprise', price: 'Soon', items: ['SSO', 'Audit trails', 'Custom weights'] },
          ].map((p) => (
            <Card
              key={p.name}
              className={p.highlight ? 'border-accent/40 ring-1 ring-accent/30' : ''}
            >
              <p className="text-sm font-semibold text-accent">{p.name}</p>
              <p className="mt-2 font-display text-4xl font-semibold">{p.price}</p>
              <ul className="mt-5 space-y-2">
                {p.items.map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Check className="h-4 w-4 text-accent" /> {item}
                  </li>
                ))}
              </ul>
              <Button className="mt-6 w-full" variant={p.highlight ? 'default' : 'secondary'} asChild>
                <Link to="/login">Start</Link>
              </Button>
            </Card>
          ))}
        </div>
      </section>

      <section className="relative z-10 mx-auto max-w-3xl px-4 pb-20">
        <h2 className="mb-6 font-display text-3xl font-semibold">FAQ</h2>
        <div className="space-y-2">
          {faqs.map((f, i) => (
            <button
              key={f.q}
              type="button"
              onClick={() => setOpenFaq(openFaq === i ? -1 : i)}
              className="glass w-full rounded-2xl px-5 py-4 text-left"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium">{f.q}</span>
                <ChevronDown
                  className={`h-4 w-4 transition ${openFaq === i ? 'rotate-180' : ''}`}
                />
              </div>
              {openFaq === i ? (
                <p className="mt-2 text-sm text-muted-foreground">{f.a}</p>
              ) : null}
            </button>
          ))}
        </div>
      </section>

      <footer className="relative z-10 border-t border-border bg-card/30 py-10">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-accent" />
            <span className="font-display font-semibold">ScreenWise</span>
          </div>
          <p className="text-sm text-muted-foreground">
            AI CV screening & ranking
          </p>
          <Link to="/login" className="text-sm font-semibold text-accent hover:underline">
            Open portals →
          </Link>
        </div>
      </footer>
    </div>
  );
}
