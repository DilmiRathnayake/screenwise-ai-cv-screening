import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff, Loader2, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '../../api/endpoints';
import { getErrorMessage } from '../../api/client';
import { homePathForUser, setAuth } from '../../store/authStore';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';

const REMEMBER_KEY = 'screenwise_remember_email';

const COPY = {
  admin: {
    title: 'Admin console',
    subtitle: 'Oversee ScreenWise health, usage, and hiring operations.',
    panelTitle: 'Command the platform',
    panelBody: 'Monitor AI readiness, recruitment volume, and system signals in one glass surface.',
    defaultEmail: 'admin@cvscreening.local',
  },
  hr: {
    title: 'HR workspace',
    subtitle: 'Screen CVs, rank talent, and schedule interviews.',
    panelTitle: 'Hire with clarity',
    panelBody: 'Explainable scores, semantic search, and interview calendars — built for recruiters.',
    defaultEmail: 'hr@cvscreening.local',
  },
  candidate: {
    title: 'Candidate portal',
    subtitle: 'Track applications and interview readiness.',
    panelTitle: 'Your career cockpit',
    panelBody: 'See real application status, AI feedback, and interview schedules linked to your email.',
    defaultEmail: 'candidate@cvscreening.local',
  },
};

export default function RoleLoginPage({ role = 'hr' }) {
  const cfg = COPY[role] || COPY.hr;
  const navigate = useNavigate();
  const [showPw, setShowPw] = useState(false);
  const [remember, setRemember] = useState(true);
  const [step, setStep] = useState('login'); // login | forgot | otp
  const [otp, setOtp] = useState(['', '', '', '', '', '']);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    defaultValues: {
      email: cfg.defaultEmail,
      password: 'Password123!',
    },
  });

  useEffect(() => {
    const saved = localStorage.getItem(REMEMBER_KEY);
    if (saved) {
      setValue('email', saved);
      setRemember(true);
    }
  }, [setValue]);

  async function onSubmit(values) {
    try {
      const res = await authApi.login(values);
      const user = res.data.user;
      if (role === 'admin' && user.role !== 'admin') {
        toast.error('This portal is for administrators only');
        return;
      }
      if (role === 'hr' && user.role !== 'hr' && user.role !== 'admin') {
        toast.error('HR credentials required');
        return;
      }
      if (role === 'candidate' && user.role !== 'candidate') {
        toast.error('Candidate credentials required');
        return;
      }
      if (remember) localStorage.setItem(REMEMBER_KEY, values.email);
      else localStorage.removeItem(REMEMBER_KEY);
      setAuth(res.data.token, user);
      toast.success('Welcome back');
      navigate(homePathForUser(user));
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  }

  function sendForgot() {
    toast('Demo — email reset is not connected to a mail service', { icon: '✉️' });
    setStep('otp');
  }

  function verifyOtp() {
    toast('Demo — OTP verification UI only', { icon: '🔐' });
    setStep('login');
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden lg:block">
        <div className="absolute inset-0 mesh-bg bg-background" />
        <motion.div
          className="absolute left-16 top-24 h-64 w-64 rounded-full bg-accent/30 blur-3xl"
          animate={{ y: [0, 40, 0] }}
          transition={{ duration: 9, repeat: Infinity }}
        />
        <div className="relative flex h-full flex-col justify-between p-12">
          <Link to="/" className="font-display text-2xl font-semibold">
            ScreenWise
          </Link>
          <div>
            <h1 className="max-w-md font-display text-4xl font-semibold leading-tight">
              {cfg.panelTitle}
            </h1>
            <p className="mt-4 max-w-md text-muted-foreground">{cfg.panelBody}</p>
          </div>
          <p className="text-sm text-muted-foreground">Premium recruiting intelligence</p>
        </div>
      </div>

      <div className="relative flex items-center justify-center px-4 py-12">
        <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-sky-500/5" />
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass relative w-full max-w-md rounded-3xl p-7"
        >
          <Link
            to="/login"
            className="mb-5 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> All portals
          </Link>

          <AnimatePresence mode="wait">
            {step === 'login' ? (
              <motion.form
                key="login"
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                onSubmit={handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <div>
                  <h2 className="font-display text-2xl font-semibold">{cfg.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{cfg.subtitle}</p>
                </div>
                <Input
                  label="Email"
                  type="email"
                  autoComplete="email"
                  error={errors.email?.message}
                  {...register('email', { required: 'Email is required' })}
                />
                <div className="relative">
                  <Input
                    label="Password"
                    type={showPw ? 'text' : 'password'}
                    autoComplete="current-password"
                    error={errors.password?.message}
                    {...register('password', { required: 'Password is required' })}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-[38px] text-muted-foreground hover:text-foreground"
                    onClick={() => setShowPw((s) => !s)}
                    aria-label="Toggle password"
                  >
                    {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <label className="flex items-center gap-2 text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                      className="rounded border-border"
                    />
                    Remember me
                  </label>
                  <button
                    type="button"
                    className="font-medium text-accent hover:underline"
                    onClick={() => setStep('forgot')}
                  >
                    Forgot password
                  </button>
                </div>
                <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  Sign in
                </Button>
                <p className="text-center text-sm text-muted-foreground">
                  {role === 'candidate' ? (
                    <>
                      New candidate?{' '}
                      <Link
                        to="/register/candidate"
                        className="font-semibold text-accent hover:underline"
                      >
                        Register
                      </Link>
                    </>
                  ) : (
                    <>
                      Need an HR account?{' '}
                      <Link to="/register" className="font-semibold text-accent hover:underline">
                        Register
                      </Link>
                    </>
                  )}
                </p>
              </motion.form>
            ) : null}

            {step === 'forgot' ? (
              <motion.div
                key="forgot"
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                className="space-y-4"
              >
                <h2 className="font-display text-2xl font-semibold">Reset password</h2>
                <p className="text-sm text-muted-foreground">
                  Enter your email — we&apos;ll show the OTP step (demo only).
                </p>
                <Input label="Email" type="email" defaultValue={cfg.defaultEmail} />
                <Button className="w-full" onClick={sendForgot}>
                  Send reset code
                </Button>
                <Button variant="ghost" className="w-full" onClick={() => setStep('login')}>
                  Back to sign in
                </Button>
              </motion.div>
            ) : null}

            {step === 'otp' ? (
              <motion.div
                key="otp"
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                className="space-y-4"
              >
                <h2 className="font-display text-2xl font-semibold">Verify email</h2>
                <p className="text-sm text-muted-foreground">Enter the 6-digit code (demo UI).</p>
                <div className="flex justify-between gap-2">
                  {otp.map((d, i) => (
                    <input
                      key={i}
                      value={d}
                      maxLength={1}
                      onChange={(e) => {
                        const next = [...otp];
                        next[i] = e.target.value.replace(/\D/g, '').slice(-1);
                        setOtp(next);
                      }}
                      className="h-12 w-10 rounded-xl border border-border bg-background/70 text-center text-lg font-semibold"
                    />
                  ))}
                </div>
                <Button className="w-full" onClick={verifyOtp}>
                  Verify OTP
                </Button>
                <Button variant="ghost" className="w-full" onClick={() => setStep('login')}>
                  Cancel
                </Button>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
