import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DataTable, type DataTableColumn } from '../../components/data/DataTable'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { HealthStatusBadge } from '../../components/data/HealthStatusBadge'
import { SearchInput } from '../../components/data/SearchInput'
import { PageHeader } from '../../components/layout/PageHeader'
import { useDiagnosticsList } from '../../hooks/useDiagnostics'
import { formatDateTime } from '../../lib/utils'
import type { Diagnostic } from '../../types/api'

export function HistoryPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const listQuery = useDiagnosticsList({ code: code.trim() || undefined, limit: 50 })

  const columns: DataTableColumn<Diagnostic>[] = [
    { key: 'vehicle_code', header: 'Vehicle', accessor: (d) => d.vehicle_code, sortable: true },
    { key: 'battery_serial', header: 'Battery', accessor: (d) => d.battery_serial, sortable: true },
    {
      key: 'predicted_class',
      header: 'Result',
      accessor: (d) => d.predicted_class,
      sortable: true,
      render: (d) => <HealthStatusBadge healthClass={d.predicted_class} size="sm" />,
    },
    { key: 'model_version', header: 'Model', accessor: (d) => `${d.model_algorithm} ${d.model_version}`, sortable: true },
    { key: 'technician_name', header: 'Technician', accessor: (d) => d.technician_name ?? 'Unknown', sortable: true },
    { key: 'created_at', header: 'When', accessor: (d) => d.created_at, sortable: true, render: (d) => formatDateTime(d.created_at) },
  ]

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="History" description="All diagnostics you have access to." />

      <SearchInput
        label="Filter by vehicle code or battery serial"
        hideLabel={false}
        placeholder="e.g. EV100042"
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />

      {listQuery.isLoading && <LoadingSkeleton variant="table" rows={6} />}
      {listQuery.isError && <ErrorState error={listQuery.error} onRetry={() => listQuery.refetch()} />}

      {listQuery.data && (
        <DataTable
          caption="Diagnostic history"
          columns={columns}
          rows={listQuery.data}
          getRowId={(d) => d.id}
          onRowClick={(d) => navigate(`/tech/diagnostics/${d.id}`, { state: { diagnostic: d } })}
          emptyTitle="No diagnostics found"
          emptyDescription={code ? `No results for "${code}".` : 'Run a diagnostic from the Lookup page.'}
        />
      )}
    </div>
  )
}
