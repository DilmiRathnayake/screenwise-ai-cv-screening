import { forwardRef } from 'react';
import { cn } from '../../lib/utils';

export const Select = forwardRef(function Select(
  { className, label, error, children, ...props },
  ref
) {
  return (
    <label className="block space-y-1.5">
      {label ? (
        <span className="text-sm font-medium text-foreground/90">{label}</span>
      ) : null}
      <select
        ref={ref}
        className={cn(
          'flex h-11 w-full rounded-xl border border-border bg-background/60 px-3.5 text-sm text-foreground transition focus:border-accent/50',
          error && 'border-destructive/60',
          className
        )}
        {...props}
      >
        {children}
      </select>
      {error ? <span className="text-xs text-destructive">{error}</span> : null}
    </label>
  );
});
