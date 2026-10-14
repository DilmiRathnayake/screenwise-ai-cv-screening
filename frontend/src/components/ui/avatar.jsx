import * as Avatar from '@radix-ui/react-avatar';
import { cn, initials } from '../../lib/utils';

export function UserAvatar({ name, src, className, size = 'md' }) {
  const sizes = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-14 w-14 text-base',
    xl: 'h-20 w-20 text-xl',
  };
  return (
    <Avatar.Root
      className={cn(
        'inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-[var(--sw-accent-soft)] font-semibold text-accent',
        sizes[size],
        className
      )}
    >
      {src ? <Avatar.Image src={src} alt={name} className="h-full w-full object-cover" /> : null}
      <Avatar.Fallback delayMs={src ? 400 : 0}>{initials(name)}</Avatar.Fallback>
    </Avatar.Root>
  );
}
