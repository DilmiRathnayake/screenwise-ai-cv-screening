import { cn } from '../../lib/utils';

export function Card({ className, children, hover = false, ...props }) {
  return (
    <div
      className={cn(
        'glass rounded-2xl p-5 transition-all duration-300',
        hover && 'hover:-translate-y-0.5 hover:shadow-xl',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children }) {
  return <div className={cn('mb-4 flex items-start justify-between gap-3', className)}>{children}</div>;
}

export function CardTitle({ className, children }) {
  return (
    <h3 className={cn('font-display text-lg font-semibold tracking-tight', className)}>
      {children}
    </h3>
  );
}

export function CardDescription({ className, children }) {
  return (
    <p className={cn('text-sm text-muted-foreground', className)}>{children}</p>
  );
}
