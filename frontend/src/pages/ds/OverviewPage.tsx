import { BarChart3, Boxes, Cpu, Database, TrendingUp } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../components/layout/PageHeader'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { EmptyState } from '../../components/data/EmptyState'
import { KpiCard } from '../../components/data/KpiCard'
import { DataTable, type DataTableColumn } from '../../components/data/DataTable'
import { MetricComparisonChart, type AlgorithmMetrics } from '../../components/charts/MetricComparisonChart'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { useDatasets } from '../../hooks/useDatasets'
import { useTrainingRuns } from '../../hooks/useTraining'
import { useActiveModel } from '../../hooks/useModels'
import { ALGORITHM_LABELS } from '../../lib/chartColors'
import { formatDateTime, formatRelativeTime } from '../../lib/utils'
import type { Algorithm, TrainingRun } from '../../types/api'

export function OverviewPage() {
  const navigate = useNavigate()
  const datasetsQuery = useDatasets()
  const runsQuery = useTrainingRuns()
  const activeModelQuery = useActiveModel()

  const isLoading = datasetsQuery.isLoading || runsQuery.isLoading || activeModelQuery.isLoading
  const firstError = datasetsQuery.error ?? runsQuery.error ?? activeModelQuery.error

  if (isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Overview" description="Your Data Scientist workspace at a glance." />
        <div className="grid grid-cols-1 gap-lg sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <LoadingSkeleton key={i} variant="card" />
          ))}
        </div>
        <LoadingSkeleton variant="table" rows={4} />
      </div>
    )
  }

  if (firstError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Overview" />
        <ErrorState
          error={firstError}
          onRetry={() => {
            datasetsQuery.refetch()
            runsQuery.refetch()
            activeModelQuery.refetch()
          }}
        />
      </div>
    )
  }

  const datasets = datasetsQuery.data ?? []
  const runs = runsQuery.data ?? []
  const activeModel = activeModelQuery.data ?? null

  const completedRuns = runs.filter((r) => r.status === 'completed' && r.metrics)
  const bestAccuracy = completedRuns.reduce<number | null>((best, r) => {
    const acc = r.metrics?.accuracy ?? null
    if (acc === null) return best
    if (best === null || acc > best) return acc
    return best
  }, null)
  const latestRun = runs[0] ?? null

  if (runs.length === 0) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Overview" description="Your Data Scientist workspace at a glance." />
        <div className="grid grid-cols-1 gap-lg sm:grid-cols-2 lg:grid-cols-3">
          <KpiCard label="Datasets" value={String(datasets.length)} icon={Database} />
          <KpiCard label="Training Runs" value="0" icon={Cpu} />
          <KpiCard label="Deployed Model" value="None" icon={Boxes} />
        </div>
        <EmptyState
          icon={TrendingUp}
          title="No model trained yet"
          description="Upload a dataset and start a training run to see metrics here."
          action={
            <Button onClick={() => navigate('/ds/training')}>Go to Training</Button>
          }
        />
      </div>
    )
  }

  const bestPerAlgorithm = new Map<Algorithm, TrainingRun>()
  for (const run of completedRuns) {
    const existing = bestPerAlgorithm.get(run.algorithm)
    if (!existing || (run.metrics?.accuracy ?? 0) > (existing.metrics?.accuracy ?? 0)) {
      bestPerAlgorithm.set(run.algorithm, run)
    }
  }
  const comparisonEntries: AlgorithmMetrics[] = Array.from(bestPerAlgorithm.values()).map((r) => ({
    algorithm: r.algorithm,
    metrics: r.metrics!,
  }))

  const columns: DataTableColumn<TrainingRun>[] = [
    { key: 'algorithm', header: 'Algorithm', accessor: (r) => ALGORITHM_LABELS[r.algorithm] ?? r.algorithm },
    { key: 'dataset_name', header: 'Dataset', accessor: (r) => r.dataset_name },
    {
      key: 'status',
      header: 'Status',
      accessor: (r) => r.status,
      render: (r) => (
        <Badge tone={r.status === 'completed' ? 'good' : r.status === 'failed' ? 'critical' : 'neutral'}>
          {r.status}
        </Badge>
      ),
    },
    { key: 'started_at', header: 'Started', accessor: (r) => r.started_at, render: (r) => formatDateTime(r.started_at) },
  ]

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="Overview" description="Your Data Scientist workspace at a glance." />

      <div className="grid grid-cols-1 gap-lg sm:grid-cols-2 lg:grid-cols-5">
        <KpiCard label="Datasets" value={String(datasets.length)} icon={Database} />
        <KpiCard label="Training Runs" value={String(runs.length)} icon={Cpu} />
        <KpiCard
          label="Deployed Model"
          value={activeModel ? activeModel.version : 'None'}
          hint={activeModel ? (ALGORITHM_LABELS[activeModel.algorithm] ?? activeModel.algorithm) : 'Deploy a model to go live'}
          icon={Boxes}
        />
        <KpiCard
          label="Best Accuracy"
          value={bestAccuracy !== null ? `${(bestAccuracy * 100).toFixed(1)}` : '--'}
          unit={bestAccuracy !== null ? '%' : undefined}
          icon={TrendingUp}
        />
        <KpiCard
          label="Latest Training"
          value={latestRun ? formatRelativeTime(latestRun.started_at) : '--'}
          valueVariant="text"
          hint={latestRun ? `${formatDateTime(latestRun.started_at)} - ${latestRun.status}` : undefined}
          icon={BarChart3}
        />
      </div>

      {comparisonEntries.length > 0 && <MetricComparisonChart entries={comparisonEntries} />}

      <div>
        <h2 className="mb-md text-lg font-semibold text-text-primary">Recent training runs</h2>
        <DataTable
          caption="Recent training runs"
          columns={columns}
          rows={runs.slice(0, 5)}
          getRowId={(r) => r.id}
        />
      </div>
    </div>
  )
}
