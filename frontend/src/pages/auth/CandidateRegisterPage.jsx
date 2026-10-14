import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '../../api/endpoints';
import { getErrorMessage } from '../../api/client';
import { homePathForUser, setAuth } from '../../store/authStore';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';

export default function CandidateRegisterPage() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm();

  async function onSubmit(values) {
    try {
      const res = await authApi.register({
        email: values.email,
        password: values.password,
        fullName: values.fullName,
        role: 'candidate',
      });
      setAuth(res.data.token, res.data.user);
      toast.success('Account created');
      navigate(homePathForUser(res.data.user));
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4 py-12">
      <div className="pointer-events-none absolute inset-0 mesh-bg" />
      <motion.form
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit(onSubmit)}
        className="glass relative w-full max-w-md space-y-4 rounded-3xl p-7"
      >
        <div>
          <Link to="/" className="font-display text-xl font-semibold">
            ScreenWise
          </Link>
          <h1 className="mt-3 font-display text-2xl font-semibold">Create candidate account</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Use the same email as on your CV so HR uploads link to your dashboard.
          </p>
        </div>
        <Input
          label="Full name"
          error={errors.fullName?.message}
          {...register('fullName', { required: 'Required' })}
        />
        <Input
          label="Email"
          type="email"
          error={errors.email?.message}
          {...register('email', { required: 'Required' })}
        />
        <Input
          label="Password"
          type="password"
          error={errors.password?.message}
          {...register('password', {
            required: 'Required',
            minLength: { value: 8, message: 'Min 8 characters' },
          })}
        />
        <Input
          label="Confirm password"
          type="password"
          error={errors.confirm?.message}
          {...register('confirm', {
            validate: (v) => v === watch('password') || 'Passwords must match',
          })}
        />
        <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
          {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          Create account
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Already registered?{' '}
          <Link to="/login/candidate" className="font-semibold text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </motion.form>
    </div>
  );
}
