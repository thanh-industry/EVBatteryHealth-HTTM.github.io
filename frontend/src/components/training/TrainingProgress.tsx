import { CheckCircle2, Loader2, XCircle } from 'lucide-react'
import type { TrainingRun } from '../../types/api'
import { ALGORITHM_LABELS } from '../../lib/chartColors'
import { formatSeconds } from '../../lib/utils'

export interface TrainingProgressProps {
  run: TrainingRun
}

const STATUS_COPY: Record<TrainingRun['status'], string> = {
  pending: 'Queued - waiting to start',
  running: 'Training in progress...',
  completed: 'Training completed',
  failed: 'Training failed',
}

export function TrainingProgress({ run }: TrainingProgressProps) {
  return (
    <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
      <div className="flex items-center gap-md">
        {(run.status === 'pending' || run.status === 'running') && (
          <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
        )}
        {run.status === 'completed' && <CheckCircle2 className="h-5 w-5 text-good" aria-hidden="true" />}
        {run.status === 'failed' && <XCircle className="h-5 w-5 text-critical" aria-hidden="true" />}
        <div>
          <p className="text-sm font-semibold text-text-primary">{STATUS_COPY[run.status]}</p>
          <p className="text-caption text-text-muted">
            {ALGORITHM_LABELS[run.algorithm] ?? run.algorithm} on {run.dataset_name}
          </p>
        </div>
      </div>

      {(run.status === 'pending' || run.status === 'running') && (
        <div className="mt-lg h-md w-full overflow-hidden rounded-full bg-muted" role="progressbar" aria-label="Training progress" aria-valuetext={STATUS_COPY[run.status]}>
          <div className="h-full w-2/3 animate-pulse rounded-full bg-primary" />
        </div>
      )}

      {run.status === 'failed' && run.error && (
        <p role="alert" className="mt-lg text-sm text-critical">
          {run.error}
        </p>
      )}

      {run.status === 'completed' && (
        <dl className="mt-lg grid grid-cols-2 gap-md sm:grid-cols-4">
          <div>
            <dt className="text-caption text-text-muted">Duration</dt>
            <dd className="font-mono text-sm text-text-primary">{formatSeconds(run.duration_seconds)}</dd>
          </div>
          <div>
            <dt className="text-caption text-text-muted">Train rows</dt>
            <dd className="font-mono text-sm text-text-primary">{run.train_rows ?? '--'}</dd>
          </div>
          <div>
            <dt className="text-caption text-text-muted">Test rows</dt>
            <dd className="font-mono text-sm text-text-primary">{run.test_rows ?? '--'}</dd>
          </div>
          <div>
            <dt className="text-caption text-text-muted">Accuracy</dt>
            <dd className="font-mono text-sm text-text-primary">
              {run.metrics ? `${(run.metrics.accuracy * 100).toFixed(1)}%` : '--'}
            </dd>
          </div>
        </dl>
      )}
    </div>
  )
}
