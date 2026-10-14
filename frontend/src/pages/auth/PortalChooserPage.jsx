import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Briefcase, Shield, UserRound } from 'lucide-react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';

const portals = [
  {
    to: '/login/admin',
    title: 'Administrator',
    desc: 'System health, analytics, and platform oversight.',
    icon: Shield,
    accent: 'from-teal-500/20 to-sky-500/10',
  },
  {
    to: '/login/hr',
    title: 'HR Manager',
    desc: 'Jobs, CV screening, AI ranking, and interviews.',
    icon: Briefcase,
    accent: 'from-emerald-500/20 to-teal-500/10',
  },
  {
    to: '/login/candidate',
    title: 'Candidate',
    desc: 'Track applications, AI feedback, and interviews from live data.',
    icon: UserRound,
    accent: 'from-amber-500/20 to-orange-500/10',
  },
];

export default function PortalChooserPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-16">
      <div className="pointer-events-none absolute inset-0 mesh-bg" />
      <div className="relative z-10 w-full max-w-4xl">
        <div className="mb-10 text-center">
          <Link to="/" className="font-display text-2xl font-semibold">
            ScreenWise
          </Link>
          <h1 className="mt-4 font-display text-4xl font-semibold">Choose your portal</h1>
          <p className="mt-2 text-muted-foreground">
            Each experience is tailored — same design language, distinct workflows.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {portals.map((p, i) => (
            <motion.div
              key={p.to}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
            >
              <Card hover className={`h-full bg-gradient-to-br ${p.accent}`}>
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-background/60 text-accent">
                  <p.icon className="h-6 w-6" />
                </div>
                <h2 className="font-display text-xl font-semibold">{p.title}</h2>
                <p className="mt-2 text-sm text-muted-foreground">{p.desc}</p>
                <Button className="mt-6 w-full" asChild>
                  <Link to={p.to}>Continue</Link>
                </Button>
              </Card>
            </motion.div>
          ))}
        </div>
        <p className="mt-8 text-center text-sm text-muted-foreground">
          New HR account?{' '}
          <Link to="/register" className="font-semibold text-accent hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
