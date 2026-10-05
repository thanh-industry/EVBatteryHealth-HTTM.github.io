import type { ReactNode } from 'react'
import { ALGORITHM_LABELS } from '../../lib/chartColors'
import { formatDateTime, formatPercent } from '../../lib/utils'
import type { Metrics } from '../../types/api'
import { Badge } from '../ui/Badge'

export interface ModelCardProps {
  version: string | null
  algorithm: string
  datasetName: string
  dateLabel: string
  dateValue: string | null
  metrics: Metrics
  isActive?: boolean
  supportsProbability: boolean
  actions?: ReactNode
}

export function ModelCard({
  version,
  algorithm,
  datasetName,
  dateLabel,
  dateValue,
  metrics,
  isActive,
  supportsProbability,
  actions,
}: ModelCardProps) {
  return (
    <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
      <div className="flex items-start justify-between gap-md">
        <div>
          <div className="flex items-center gap-md">
            <h3 className="text-sm font-semibold text-text-primary">{version ?? 'Unversioned'}</h3>
            {isActive && <Badge tone="primary">Active</Badge>}
          </div>
          <p className="mt-xs text-sm text-text-secondary">{ALGORITHM_LABELS[algorithm] ?? algorithm}</p>
          <p className="text-caption text-text-muted">Trained on {datasetName}</p>
          <p className="text-caption text-text-muted">
            {dateLabel}: {formatDateTime(dateValue)}
          </p>
          {!supportsProbability && (
            <p className="mt-xs text-caption text-text-muted">Confidence: not available for this estimator</p>
          )}
        </div>
        {actions}
      </div>
      <dl className="mt-lg grid grid-cols-2 gap-md sm:grid-cols-4">
        <Metric label="Accuracy" value={metrics.accuracy} />
        <Metric label="Precision" value={metrics.precision_macro} />
        <Metric label="Recall" value={metrics.recall_macro} />
        <Metric label="F1" value={metrics.f1_macro} />
      </dl>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-caption text-text-muted">{label}</dt>
      <dd className="font-mono text-base font-semibold tabular-nums text-text-primary">
        {formatPercent(value * 100)}
      </dd>
    </div>
  )
}
