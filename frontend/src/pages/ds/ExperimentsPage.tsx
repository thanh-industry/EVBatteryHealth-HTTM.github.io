import { useState } from 'react'
import { DataTable, type DataTableColumn } from '../../components/data/DataTable'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { useTrainingRuns } from '../../hooks/useTraining'
import { ALGORITHM_LABELS } from '../../lib/chartColors'
import { formatDateTime, formatPercent, formatSeconds } from '../../lib/utils'
import type { TrainingRun } from '../../types/api'
import { ExperimentDetailPanel } from './experiments/ExperimentDetailPanel'

export function ExperimentsPage() {
  const runsQuery = useTrainingRuns()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  if (runsQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Experiments" description="Every training run, with full detail on click." />
        <LoadingSkeleton variant="table" rows={6} />
      </div>
    )
  }

  if (runsQuery.isError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Experiments" />
        <ErrorState error={runsQuery.error} onRetry={() => runsQuery.refetch()} />
      </div>
    )
  }

  const runs = runsQuery.data ?? []
  const selectedRun = runs.find((r) => r.id === selectedId) ?? null

  const columns: DataTableColumn<TrainingRun>[] = [
    { key: 'version', header: 'Version', accessor: (r) => r.version ?? `#${r.id}`, sortable: true },
    { key: 'algorithm', header: 'Algorithm', accessor: (r) => ALGORITHM_LABELS[r.algorithm] ?? r.algorithm, sortable: true },
    { key: 'dataset_name', header: 'Dataset', accessor: (r) => r.dataset_name, sortable: true },
    { key: 'test_size', header: 'Test size', accessor: (r) => r.test_size, sortable: true, numeric: true, align: 'right', render: (r) => `${(r.test_size * 100).toFixed(0)}%` },
    { key: 'duration_seconds', header: 'Duration', accessor: (r) => r.duration_seconds, sortable: true, numeric: true, align: 'right', render: (r) => formatSeconds(r.duration_seconds) },
    {
      key: 'accuracy',
      header: 'Accuracy',
      accessor: (r) => r.metrics?.accuracy ?? null,
      sortable: true,
      numeric: true,
      align: 'right',
      render: (r) => (r.metrics ? formatPercent(r.metrics.accuracy * 100) : '--'),
    },
    {
      key: 'f1_macro',
      header: 'F1',
      accessor: (r) => r.metrics?.f1_macro ?? null,
      sortable: true,
      numeric: true,
      align: 'right',
      render: (r) => (r.metrics ? formatPercent(r.metrics.f1_macro * 100) : '--'),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (r) => r.status,
      sortable: true,
      render: (r) => (
        <Badge tone={r.status === 'completed' ? 'good' : r.status === 'failed' ? 'critical' : 'neutral'}>
          {r.status}
        </Badge>
      ),
    },
    { key: 'started_at', header: 'Started', accessor: (r) => r.started_at, sortable: true, render: (r) => formatDateTime(r.started_at) },
  ]

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="Experiments" description="Every training run. Click a row for full detail." />

      <DataTable
        caption="All training runs"
        columns={columns}
        rows={runs}
        getRowId={(r) => r.id}
        onRowClick={(r) => setSelectedId(r.id === selectedId ? null : r.id)}
        selectedRowId={selectedId}
        emptyTitle="No training runs yet"
        emptyDescription="Start a training run from the Training page."
      />

      {selectedRun && <ExperimentDetailPanel run={selectedRun} onClose={() => setSelectedId(null)} />}
    </div>
  )
}
