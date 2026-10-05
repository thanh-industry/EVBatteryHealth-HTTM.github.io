import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { NotificationCenter } from '../../components/notifications/NotificationCenter'
import { Button } from '../../components/ui/Button'
import { useMarkAllNotificationsRead, useMarkNotificationRead, useNotifications } from '../../hooks/useNotifications'

export function NotificationsPage() {
  const notificationsQuery = useNotifications()
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()

  if (notificationsQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Notifications" />
        <LoadingSkeleton rows={4} />
      </div>
    )
  }

  if (notificationsQuery.isError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Notifications" />
        <ErrorState error={notificationsQuery.error} onRetry={() => notificationsQuery.refetch()} />
      </div>
    )
  }

  const notifications = notificationsQuery.data ?? []
  const hasUnread = notifications.some((n) => !n.read_at)

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader
        title="Notifications"
        actions={
          <Button
            variant="secondary"
            disabled={!hasUnread}
            disabledReason={!hasUnread ? 'No unread notifications.' : undefined}
            loading={markAllRead.isPending}
            onClick={() => markAllRead.mutate()}
          >
            Mark all read
          </Button>
        }
      />

      <NotificationCenter
        notifications={notifications}
        onMarkRead={(id) => markRead.mutate(id)}
        markingReadId={markRead.isPending ? markRead.variables ?? null : null}
      />
    </div>
  )
}
