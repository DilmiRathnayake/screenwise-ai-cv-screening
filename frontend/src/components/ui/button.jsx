import { Slot } from '@radix-ui/react-slot';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]',
  {
    variants: {
      variant: {
        default:
          'bg-accent text-accent-foreground shadow-lg shadow-accent/20 hover:brightness-110',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-muted border border-border',
        outline:
          'border border-border bg-transparent hover:bg-muted/60 text-foreground',
        ghost: 'hover:bg-muted/70 text-foreground',
        destructive:
          'bg-destructive text-white shadow-lg shadow-destructive/20 hover:brightness-110',
        soft: 'bg-[var(--sw-accent-soft)] text-accent hover:brightness-105',
      },
      size: {
        default: 'h-11 px-5',
        sm: 'h-9 rounded-lg px-3 text-xs',
        lg: 'h-12 rounded-2xl px-7 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
);

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot : 'button';
  return (
    <Comp
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}

export { buttonVariants };
