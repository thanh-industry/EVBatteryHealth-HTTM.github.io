import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { EmptyState } from '../../components/data/EmptyState'
import { PageHeader } from '../../components/layout/PageHeader'
import { MetricComparisonChart, type AlgorithmMetrics } from '../../components/charts/MetricComparisonChart'
import { ModelComparisonTable } from '../../components/models/ModelComparisonTable'
import { useTrainingRuns } from '../../hooks/useTraining'
import type { Algorithm, TrainingRun } from '../../types/api'

export function ComparePage() {
  const runsQuery = useTrainingRuns()

  if (runsQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Model Comparison" description="Accuracy, precision, recall and F1 side by side." />
        <LoadingSkeleton variant="chart" />
        <LoadingSkeleton variant="table" rows={4} />
      </div>
    )
  }

  if (runsQuery.isError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Model Comparison" />
        <ErrorState error={runsQuery.error} onRetry={() => runsQuery.refetch()} />
      </div>
    )
  }

  const runs = runsQuery.data ?? []
  const completedRuns = runs.filter((r) => r.status === 'completed' && r.metrics)

  if (completedRuns.length === 0) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Model Comparison" description="Accuracy, precision, recall and F1 side by side." />
        <EmptyState title="Nothing to compare yet" description="Complete at least one training run first." />
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
  const chartEntries: AlgorithmMetrics[] = Array.from(bestPerAlgorithm.values()).map((r) => ({
    algorithm: r.algorithm,
    metrics: r.metrics!,
  }))

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader
        title="Model Comparison"
        description="Accuracy, precision, recall and F1 side by side - no single metric declares a winner."
      />

      <MetricComparisonChart entries={chartEntries} />

      <div>
        <h2 className="mb-md text-lg font-semibold text-text-primary">All completed runs</h2>
        <ModelComparisonTable runs={completedRuns} />
      </div>
    </div>
  )
}
