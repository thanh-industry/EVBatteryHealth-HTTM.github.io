import { AlertOctagon, AlertTriangle, CheckCircle2, Info } from 'lucide-react'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { EmptyState } from '../../components/data/EmptyState'
import { PageHeader } from '../../components/layout/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { useMyMaintenance } from '../../hooks/useMe'
import { formatDate } from '../../lib/utils'
import type { MaintenanceItem } from '../../types/api'

const SEVERITY_ICON = { info: Info, warning: AlertTriangle, critical: AlertOctagon } as const
const SEVERITY_TONE = { info: 'info', warning: 'monitor', critical: 'critical' } as const

export function MaintenancePage() {
  const maintenanceQuery = useMyMaintenance()

  if (maintenanceQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Maintenance" />
        <LoadingSkeleton rows={4} />
      </div>
    )
  }

  if (maintenanceQuery.isError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Maintenance" />
        <ErrorState error={maintenanceQuery.error} onRetry={() => maintenanceQuery.refetch()} />
      </div>
    )
  }

  const items = maintenanceQuery.data ?? []

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="Maintenance" description="Recommended actions for your vehicle." />

      {items.length === 0 ? (
        <EmptyState icon={CheckCircle2} title="Nothing pending" description="No maintenance items right now." />
      ) : (
        <ul className="flex flex-col gap-md">
          {items.map((item) => (
            <MaintenanceRow key={item.id} item={item} />
          ))}
        </ul>
      )}
    </div>
  )
}

function MaintenanceRow({ item }: { item: MaintenanceItem }) {
  const Icon = SEVERITY_ICON[item.severity]
  return (
    <li className="rounded-lg border border-border bg-surface p-lg shadow-sm">
      <div className="flex items-start justify-between gap-md">
        <div className="flex items-start gap-md">
          <Icon className="mt-xs h-5 w-5 shrink-0 text-text-secondary" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-text-primary">{item.title}</p>
            <p className="mt-xs text-sm text-text-secondary">{item.description}</p>
            {item.due_at && <p className="mt-xs text-caption text-text-muted">Due {formatDate(item.due_at)}</p>}
          </div>
        </div>
        <div className="flex flex-col items-end gap-sm">
          <Badge tone={SEVERITY_TONE[item.severity]}>{item.severity}</Badge>
          {item.completed && <Badge tone="good">Completed</Badge>}
        </div>
      </div>
    </li>
  )
}
