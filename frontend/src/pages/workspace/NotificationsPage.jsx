import { useQuery } from '@tanstack/react-query';
import { Bell } from 'lucide-react';
import { notificationsApi, queryKeys } from '../../api/endpoints';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { EmptyState, PageHeader, Spinner } from '../../components/ui/misc';
import { formatDate } from '../../lib/utils';

export default function NotificationsPage() {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.notifications,
    queryFn: notificationsApi.list,
  });
  const items = data?.data || [];

  return (
    <div>
      <PageHeader
        title="Notification center"
        subtitle="Interview reminders and system messages from the backend."
      />
      {isLoading ? (
        <Spinner />
      ) : !items.length ? (
        <EmptyState
          icon={Bell}
          title="All caught up"
          description="Schedule interviews or sync workflows to generate alerts."
        />
      ) : (
        <div className="space-y-3">
          {items.map((n) => (
            <Card key={n.id} className="!p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{n.title || n.type}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{n.body || n.message}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {formatDate(n.created_at)}
                  </p>
                </div>
                <Badge variant={n.read_at ? 'secondary' : 'default'}>
                  {n.read_at ? 'Read' : 'New'}
                </Badge>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
