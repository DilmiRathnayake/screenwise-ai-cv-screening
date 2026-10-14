import * as Tabs from '@radix-ui/react-tabs';
import { cn } from '../../lib/utils';

export function TabsRoot({ className, ...props }) {
  return <Tabs.Root className={cn('w-full', className)} {...props} />;
}

export function TabsList({ className, ...props }) {
  return (
    <Tabs.List
      className={cn(
        'inline-flex h-11 items-center gap-1 rounded-xl border border-border bg-muted/50 p-1',
        className
      )}
      {...props}
    />
  );
}

export function TabsTrigger({ className, ...props }) {
  return (
    <Tabs.Trigger
      className={cn(
        'inline-flex items-center justify-center rounded-lg px-3.5 py-1.5 text-sm font-medium text-muted-foreground transition data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow-sm',
        className
      )}
      {...props}
    />
  );
}

export function TabsContent({ className, ...props }) {
  return <Tabs.Content className={cn('mt-4 outline-none', className)} {...props} />;
}
