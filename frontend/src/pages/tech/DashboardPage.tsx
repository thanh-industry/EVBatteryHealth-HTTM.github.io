import { AlertOctagon, AlertTriangle, ClipboardList, ShieldCheck } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { DataTable, type DataTableColumn } from '../../components/data/DataTable'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { KpiCard } from '../../components/data/KpiCard'
import { HealthStatusBadge } from '../../components/data/HealthStatusBadge'
import { PageHeader } from '../../components/layout/PageHeader'
import { Button } from '../../components/ui/Button'
import { useDiagnosticsSummary } from '../../hooks/useDiagnostics'
import { formatDateTime } from '../../lib/utils'
import type { Diagnostic } from '../../types/api'

export function DashboardPage() {
  const navigate = useNavigate()
  const summaryQuery = useDiagnosticsSummary()

  if (summaryQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Dashboard" description="Today's diagnostics at a glance." />
        <div className="grid grid-cols-2 gap-lg sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <LoadingSkeleton key={i} variant="card" />
          ))}
        </div>
        <LoadingSkeleton variant="table" rows={5} />
      </div>
    )
  }

  if (summaryQuery.isError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Dashboard" />
        <ErrorState error={summaryQuery.error} onRetry={() => summaryQuery.refetch()} />
      </div>
    )
  }

  const summary = summaryQuery.data
  if (!summary) return null

  const columns: DataTableColumn<Diagnostic>[] = [
    { key: 'vehicle_code', header: 'Vehicle', accessor: (d) => d.vehicle_code, sortable: true },
    {
      key: 'predicted_class',
      header: 'Result',
      accessor: (d) => d.predicted_class,
      sortable: true,
      render: (d) => <HealthStatusBadge healthClass={d.predicted_class} size="sm" />,
    },
    { key: 'created_at', header: 'When', accessor: (d) => d.created_at, sortable: true, render: (d) => formatDateTime(d.created_at) },
  ]

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader
        title="Dashboard"
        description="Today's diagnostics at a glance."
        actions={<Button onClick={() => navigate('/tech/lookup')}>Run a diagnostic</Button>}
      />

      <div className="grid grid-cols-2 gap-lg sm:grid-cols-4">
        <KpiCard label="Today" value={String(summary.today_count)} icon={ClipboardList} />
        <KpiCard label="Good" value={String(summary.good_count)} icon={ShieldCheck} tone="good" />
        <KpiCard label="Needs Monitoring" value={String(summary.monitor_count)} icon={AlertTriangle} tone="monitor" />
        <KpiCard label="Dangerous" value={String(summary.critical_count)} icon={AlertOctagon} tone="critical" />
      </div>

      <div>
        <h2 className="mb-md text-lg font-semibold text-text-primary">Recent diagnostics</h2>
        <DataTable
          caption="Recent diagnostics"
          columns={columns}
          rows={summary.recent}
          getRowId={(d) => d.id}
          onRowClick={(d) => navigate(`/tech/diagnostics/${d.id}`, { state: { diagnostic: d } })}
          emptyTitle="No diagnostics yet"
          emptyDescription="Run a diagnostic from the Lookup page."
        />
      </div>
    </div>
  )
}
