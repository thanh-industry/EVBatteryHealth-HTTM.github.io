import { AlertOctagon } from 'lucide-react'
import type { TrainingRun } from '../../types/api'
import { ALGORITHM_LABELS } from '../../lib/chartColors'
import { formatDateTime, formatPercent } from '../../lib/utils'
import { DataTable, type DataTableColumn } from '../data/DataTable'
import { Badge } from '../ui/Badge'
import { cx } from '../../lib/utils'

export interface ModelComparisonTableProps {
  runs: TrainingRun[]
}

type MetricKey = 'accuracy' | 'precision_macro' | 'recall_macro' | 'f1_macro'

function criticalRecall(run: TrainingRun): number | null {
  const entry = run.metrics?.per_class.find((pc) => pc.class === 'CRITICAL')
  return entry ? entry.recall : null
}

function bestRunId(runs: TrainingRun[], key: MetricKey): number | null {
  let bestId: number | null = null
  let bestValue = -Infinity
  for (const run of runs) {
    const value = run.metrics?.[key]
    if (value !== undefined && value !== null && value > bestValue) {
      bestValue = value
      bestId = run.id
    }
  }
  return bestId
}

function bestRunIdByCriticalRecall(runs: TrainingRun[]): number | null {
  let bestId: number | null = null
  let bestValue = -Infinity
  for (const run of runs) {
    const value = criticalRecall(run)
    if (value !== null && value > bestValue) {
      bestValue = value
      bestId = run.id
    }
  }
  return bestId
}

/**
 * Comparison table across all four macro metrics PLUS per-class CRITICAL
 * recall. Each metric's best value is highlighted independently - accuracy
 * alone never declares a winner (ARCHITECTURE.md section 3 /
 * DESIGN_SYSTEM.md section 5). CRITICAL recall matters separately from the
 * macro metrics: for a battery safety product, missing a dangerous battery
 * is the expensive error, so the highest-accuracy model is not
 * automatically the right deployment choice.
 */
export function ModelComparisonTable({ runs }: ModelComparisonTableProps) {
  const bestAccuracy = bestRunId(runs, 'accuracy')
  const bestPrecision = bestRunId(runs, 'precision_macro')
  const bestRecall = bestRunId(runs, 'recall_macro')
  const bestF1 = bestRunId(runs, 'f1_macro')
  const bestCriticalRecall = bestRunIdByCriticalRecall(runs)

  const metricCell = (run: TrainingRun, key: MetricKey, bestId: number | null) => {
    const value = run.metrics?.[key]
    const isBest = run.id === bestId && value !== undefined && value !== null
    return (
      <span className={cx(isBest && 'font-semibold text-good')}>
        {value !== undefined && value !== null ? formatPercent(value * 100) : '--'}
      </span>
    )
  }

  const columns: DataTableColumn<TrainingRun>[] = [
    {
      key: 'version',
      header: 'Version',
      accessor: (r) => r.version,
      sortable: true,
      render: (r) => (
        <span className="flex items-center gap-sm font-medium text-text-primary">
          {r.version ?? '--'}
          {r.is_deployed && <Badge tone="primary">Active</Badge>}
        </span>
      ),
    },
    {
      key: 'algorithm',
      header: 'Algorithm',
      accessor: (r) => ALGORITHM_LABELS[r.algorithm] ?? r.algorithm,
      sortable: true,
    },
    { key: 'dataset_name', header: 'Dataset', accessor: (r) => r.dataset_name, sortable: true },
    {
      key: 'accuracy',
      header: 'Accuracy',
      accessor: (r) => r.metrics?.accuracy ?? null,
      sortable: true,
      numeric: true,
      align: 'right',
      render: (r) => metricCell(r, 'accuracy', bestAccuracy),
    },
    {
      key: 'precision_macro',
      header: 'Precision',
      accessor: (r) => r.metrics?.precision_macro ?? null,
      sortable: true,
      numeric: true,
      align: 'right',
      render: (r) => metricCell(r, 'precision_macro', bestPrecision),
    },
    {
      key: 'recall_macro',
      header: 'Recall',
      accessor: (r) => r.metrics?.recall_macro ?? null,
      sortable: true,
      numeric: true,
      align: 'right',
      render: (r) => metricCell(r, 'recall_macro', bestRecall),
    },
    {
      key: 'f1_macro',
      header: 'F1',
      accessor: (r) => r.metrics?.f1_macro ?? null,
      sortable: true,
      numeric: true,
      align: 'right',
      render: (r) => metricCell(r, 'f1_macro', bestF1),
    },
    {
      key: 'critical_recall',
      header: 'Critical Recall',
      accessor: (r) => criticalRecall(r),
      sortable: true,
      numeric: true,
      align: 'right',
      render: (r) => {
        const value = criticalRecall(r)
        const isBest = r.id === bestCriticalRecall && value !== null
        return (
          <span className={cx('inline-flex items-center gap-xs', isBest && 'font-semibold text-good')}>
            <AlertOctagon className="h-3.5 w-3.5 shrink-0 text-critical" aria-hidden="true" />
            {value !== null ? formatPercent(value * 100) : '--'}
          </span>
        )
      },
    },
    {
      key: 'completed_at',
      header: 'Trained',
      accessor: (r) => r.completed_at,
      sortable: true,
      render: (r) => formatDateTime(r.completed_at),
    },
  ]

  return (
    <DataTable
      caption="Trained model comparison across accuracy, precision, recall, F1 and critical-class recall"
      columns={columns}
      rows={runs}
      getRowId={(r) => r.id}
      emptyTitle="No trained models yet"
      emptyDescription="Run a training job to see models here."
    />
  )
}
