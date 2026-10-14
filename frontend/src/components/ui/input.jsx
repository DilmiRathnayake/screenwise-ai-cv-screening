import { forwardRef } from 'react';
import { cn } from '../../lib/utils';

export const Input = forwardRef(function Input(
  { className, label, error, hint, ...props },
  ref
) {
  return (
    <label className="block space-y-1.5">
      {label ? (
        <span className="text-sm font-medium text-foreground/90">{label}</span>
      ) : null}
      <input
        ref={ref}
        className={cn(
          'flex h-11 w-full rounded-xl border border-border bg-background/60 px-3.5 text-sm text-foreground placeholder:text-muted-foreground transition focus:border-accent/50 focus:bg-background',
          error && 'border-destructive/60',
          className
        )}
        {...props}
      />
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
      {!error && hint ? (
        <span className="text-xs text-muted-foreground">{hint}</span>
      ) : null}
    </label>
  );
});

export const Textarea = forwardRef(function Textarea(
  { className, label, error, ...props },
  ref
) {
  return (
    <label className="block space-y-1.5">
      {label ? (
        <span className="text-sm font-medium text-foreground/90">{label}</span>
      ) : null}
      <textarea
        ref={ref}
        className={cn(
          'min-h-28 w-full rounded-xl border border-border bg-background/60 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground transition focus:border-accent/50',
          error && 'border-destructive/60',
          className
        )}
        {...props}
      />
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
    </label>
  );
});
