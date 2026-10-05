import { X } from 'lucide-react'
import type { TrainingRun } from '../../../types/api'
import { ConfusionMatrixTable } from '../../../components/models/ConfusionMatrixTable'
import { FeatureImportanceChart } from '../../../components/charts/FeatureImportanceChart'
import { Badge } from '../../../components/ui/Badge'
import { ALGORITHM_LABELS } from '../../../lib/chartColors'
import { formatDateTime, formatPercent, formatSeconds } from '../../../lib/utils'

export function ExperimentDetailPanel({ run, onClose }: { run: TrainingRun; onClose: () => void }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-xl shadow-md">
      <div className="mb-lg flex items-start justify-between gap-md">
        <div>
          <div className="flex items-center gap-md">
            <h2 className="text-lg font-semibold text-text-primary">
              {run.version ?? `Run #${run.id}`}
            </h2>
            {run.is_deployed && <Badge tone="primary">Active</Badge>}
            <Badge tone={run.status === 'completed' ? 'good' : run.status === 'failed' ? 'critical' : 'neutral'}>
              {run.status}
            </Badge>
          </div>
          <p className="text-sm text-text-secondary">
            {ALGORITHM_LABELS[run.algorithm] ?? run.algorithm} - {run.dataset_name}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close run details"
          className="flex h-[44px] w-[44px] items-center justify-center rounded-md text-text-muted hover:bg-muted"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      <dl className="mb-xl grid grid-cols-2 gap-md sm:grid-cols-4">
        <Stat label="Test size" value={`${(run.test_size * 100).toFixed(0)}%`} />
        <Stat label="Duration" value={formatSeconds(run.duration_seconds)} />
        <Stat label="Train / test rows" value={`${run.train_rows ?? '--'} / ${run.test_rows ?? '--'}`} />
        <Stat label="Started" value={formatDateTime(run.started_at)} />
      </dl>

      {run.status === 'failed' && run.error && (
        <p role="alert" className="mb-xl text-sm text-critical">
          {run.error}
        </p>
      )}

      {run.params && Object.keys(run.params).length > 0 && (
        <div className="mb-xl">
          <h3 className="mb-sm text-sm font-semibold text-text-primary">Hyperparameters</h3>
          <div className="flex flex-wrap gap-sm">
            {Object.entries(run.params).map(([key, value]) => (
              <Badge key={key} tone="neutral">
                {key}: {String(value)}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {run.metrics && (
        <div className="mb-xl">
          <h3 className="mb-md text-sm font-semibold text-text-primary">Per-class metrics</h3>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full min-w-[480px] border-collapse text-sm">
              <caption className="sr-only">Per-class precision, recall, F1 and support</caption>
              <thead>
                <tr className="border-b border-border bg-muted">
                  <th scope="col" className="px-lg py-md text-left font-semibold text-text-secondary">Class</th>
                  <th scope="col" className="px-lg py-md text-right font-semibold text-text-secondary">Precision</th>
                  <th scope="col" className="px-lg py-md text-right font-semibold text-text-secondary">Recall</th>
                  <th scope="col" className="px-lg py-md text-right font-semibold text-text-secondary">F1</th>
                  <th scope="col" className="px-lg py-md text-right font-semibold text-text-secondary">Support</th>
                </tr>
              </thead>
              <tbody>
                {run.metrics.per_class.map((row) => (
                  <tr key={row.class} className="border-b border-border last:border-0">
                    <td className="px-lg py-md font-medium text-text-primary">{row.class}</td>
                    <td className="px-lg py-md text-right font-mono tabular-nums text-text-primary">{formatPercent(row.precision * 100)}</td>
                    <td className="px-lg py-md text-right font-mono tabular-nums text-text-primary">{formatPercent(row.recall * 100)}</td>
                    <td className="px-lg py-md text-right font-mono tabular-nums text-text-primary">{formatPercent(row.f1 * 100)}</td>
                    <td className="px-lg py-md text-right font-mono tabular-nums text-text-primary">{row.support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {run.confusion_matrix && (
        <div className="mb-xl">
          <h3 className="mb-md text-sm font-semibold text-text-primary">Confusion matrix</h3>
          <ConfusionMatrixTable confusionMatrix={run.confusion_matrix} />
        </div>
      )}

      <FeatureImportanceChart features={run.feature_importance ?? []} />
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-caption text-text-muted">{label}</dt>
      <dd className="font-mono text-sm font-semibold tabular-nums text-text-primary">{value}</dd>
    </div>
  )
}
