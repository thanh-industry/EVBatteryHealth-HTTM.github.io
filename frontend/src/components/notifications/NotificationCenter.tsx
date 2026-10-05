import { AlertOctagon, AlertTriangle, Info } from 'lucide-react'
import type { Notification } from '../../types/api'
import { formatDateTime, cx } from '../../lib/utils'
import { EmptyState } from '../data/EmptyState'
import { Button } from '../ui/Button'

export interface NotificationCenterProps {
  notifications: Notification[]
  onMarkRead: (id: number) => void
  markingReadId?: number | null
}

const SEVERITY_ICON = {
  info: Info,
  warning: AlertTriangle,
  critical: AlertOctagon,
} as const

const SEVERITY_CLASS = {
  info: 'text-info',
  warning: 'text-monitor',
  critical: 'text-critical',
} as const

export function NotificationCenter({ notifications, onMarkRead, markingReadId }: NotificationCenterProps) {
  if (notifications.length === 0) {
    return <EmptyState title="No notifications" description="You are all caught up." />
  }

  return (
    <ul className="flex flex-col gap-md">
      {notifications.map((n) => {
        const Icon = SEVERITY_ICON[n.severity]
        const unread = !n.read_at
        return (
          <li
            key={n.id}
            className={cx(
              'rounded-lg border border-border bg-surface p-lg shadow-sm',
              unread && 'border-l-4 border-l-primary',
            )}
          >
            <div className="flex items-start justify-between gap-md">
              <div className="flex items-start gap-md">
                <Icon className={cx('mt-xs h-5 w-5 shrink-0', SEVERITY_CLASS[n.severity])} aria-hidden="true" />
                <div>
                  <p className="text-sm font-semibold text-text-primary">{n.title}</p>
                  <p className="mt-xs text-sm text-text-secondary">{n.body}</p>
                  <p className="mt-xs text-caption text-text-muted">{formatDateTime(n.created_at)}</p>
                </div>
              </div>
              {unread && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onMarkRead(n.id)}
                  loading={markingReadId === n.id}
                >
                  Mark read
                </Button>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
