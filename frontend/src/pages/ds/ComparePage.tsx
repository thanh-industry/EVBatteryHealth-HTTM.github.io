import { AlertOctagon } from 'lucide-react'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { EmptyState } from '../../components/data/EmptyState'
import { PageHeader } from '../../components/layout/PageHeader'
import { MetricComparisonChart, type AlgorithmMetrics } from '../../components/charts/MetricComparisonChart'
import { ModelComparisonTable } from '../../components/models/ModelComparisonTable'
import { useTrainingRuns } from '../../hooks/useTraining'
import { ALGORITHM_LABELS } from '../../lib/chartColors'
import { formatPercent } from '../../lib/utils'
import type { Algorithm, TrainingRun } from '../../types/api'

function criticalRecallOf(run: TrainingRun): number | null {
  const entry = run.metrics?.per_class.find((pc) => pc.class === 'CRITICAL')
  return entry ? entry.recall : null
}

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

  const candidates = Array.from(bestPerAlgorithm.values())
  const bestAccuracyRun = candidates.reduce<TrainingRun | null>((best, r) => {
    const acc = r.metrics?.accuracy ?? -1
    return !best || acc > (best.metrics?.accuracy ?? -1) ? r : best
  }, null)
  const bestCriticalRecallRun = candidates.reduce<TrainingRun | null>((best, r) => {
    const recall = criticalRecallOf(r) ?? -1
    return !best || recall > (criticalRecallOf(best) ?? -1) ? r : best
  }, null)
  const showTradeoffNote =
    bestAccuracyRun &&
    bestCriticalRecallRun &&
    bestAccuracyRun.algorithm !== bestCriticalRecallRun.algorithm &&
    criticalRecallOf(bestAccuracyRun) !== null &&
    criticalRecallOf(bestCriticalRecallRun) !== null

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader
        title="Model Comparison"
        description="Accuracy, precision, recall and F1 side by side - no single metric declares a winner."
      />

      {showTradeoffNote && bestAccuracyRun && bestCriticalRecallRun && (
        <div className="flex items-start gap-md rounded-lg border border-monitor bg-monitor-bg p-lg">
          <AlertOctagon className="mt-xs h-5 w-5 shrink-0 text-monitor" aria-hidden="true" />
          <p className="text-sm text-text-primary">
            <strong>{ALGORITHM_LABELS[bestAccuracyRun.algorithm] ?? bestAccuracyRun.algorithm}</strong> has the
            highest accuracy ({formatPercent((bestAccuracyRun.metrics?.accuracy ?? 0) * 100)}), but{' '}
            <strong>{ALGORITHM_LABELS[bestCriticalRecallRun.algorithm] ?? bestCriticalRecallRun.algorithm}</strong>{' '}
            catches more CRITICAL (dangerous) batteries ({formatPercent((criticalRecallOf(bestCriticalRecallRun) ?? 0) * 100)}{' '}
            recall vs {formatPercent((criticalRecallOf(bestAccuracyRun) ?? 0) * 100)}). For a battery safety product,
            a missed dangerous battery is the expensive error, so the highest-accuracy model is not automatically
            the right deployment choice - see the Critical Recall column below.
          </p>
        </div>
      )}

      <MetricComparisonChart entries={chartEntries} />

      <div>
        <h2 className="mb-md text-lg font-semibold text-text-primary">All completed runs</h2>
        <ModelComparisonTable runs={completedRuns} />
      </div>
    </div>
  )
}
