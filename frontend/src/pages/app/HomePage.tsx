import { Bell, Wrench } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { SohGauge } from '../../components/charts/SohGauge'
import { HealthStatusBadge } from '../../components/data/HealthStatusBadge'
import { TrendChart } from '../../components/charts/TrendChart'
import { useMyBattery } from '../../hooks/useMe'
import { useNotifications } from '../../hooks/useNotifications'
import { useThresholds } from '../../hooks/useThresholds'
import { formatDateTime } from '../../lib/utils'

export function HomePage() {
  const batteryQuery = useMyBattery()
  const notificationsQuery = useNotifications()
  const thresholdsQuery = useThresholds()

  if (batteryQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="My Battery" />
        <LoadingSkeleton variant="card" />
      </div>
    )
  }

  if (batteryQuery.isError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="My Battery" />
        <ErrorState error={batteryQuery.error} onRetry={() => batteryQuery.refetch()} />
      </div>
    )
  }

  const overview = batteryQuery.data
  if (!overview) return null

  const unreadCount = notificationsQuery.data?.filter((n) => !n.read_at).length ?? 0

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="My Battery" description={overview.vehicle.vehicle_code} />

      <div className="flex flex-col items-center gap-md rounded-lg border border-border bg-surface p-xl shadow-sm">
        <SohGauge soh={overview.current_soh} healthClass={overview.health_class} />
        {overview.soh_change_30d !== null && (
          <p className="text-caption text-text-muted">
            {overview.soh_change_30d <= 0 ? 'Down' : 'Up'} {Math.abs(overview.soh_change_30d).toFixed(1)} points in the last 30 days
          </p>
        )}
        <p className="text-caption text-text-muted">Last checked {formatDateTime(overview.last_checked_at)}</p>
      </div>

      <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
        <div className="mb-md flex items-center justify-between">
          <h2 className="flex items-center gap-sm text-sm font-semibold text-text-primary">
            <Bell className="h-4 w-4" aria-hidden="true" /> Alerts
          </h2>
          <Link to="/app/notifications" className="text-sm font-medium text-primary hover:underline">
            View all
          </Link>
        </div>
        <p className="text-sm text-text-secondary">
          {unreadCount === 0 ? 'No unread alerts.' : `${unreadCount} unread alert${unreadCount === 1 ? '' : 's'}.`}
        </p>
      </div>

      <div>
        <h2 className="mb-md text-sm font-semibold text-text-primary">Recent history</h2>
        <TrendChart measurements={overview.history} thresholds={thresholdsQuery.data} />
      </div>

      <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
        <h2 className="mb-md flex items-center gap-sm text-sm font-semibold text-text-primary">
          <Wrench className="h-4 w-4" aria-hidden="true" /> Recommendation
        </h2>
        <div className="mb-md">
          <HealthStatusBadge healthClass={overview.health_class} />
        </div>
        <p className="text-sm text-text-secondary">{overview.recommendation}</p>
      </div>
    </div>
  )
}
