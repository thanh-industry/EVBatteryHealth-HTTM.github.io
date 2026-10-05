import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { TrainingConfigPanel } from '../../components/training/TrainingConfigPanel'
import { TrainingProgress } from '../../components/training/TrainingProgress'
import { Button } from '../../components/ui/Button'
import { useDatasets } from '../../hooks/useDatasets'
import { useCreateTrainingRun, useTrainingRun } from '../../hooks/useTraining'
import { ApiError } from '../../lib/api'

export function TrainingPage() {
  const navigate = useNavigate()
  const datasetsQuery = useDatasets()
  const createRun = useCreateTrainingRun()
  const [activeRunId, setActiveRunId] = useState<number | null>(null)
  const activeRunQuery = useTrainingRun(activeRunId ?? undefined)

  if (datasetsQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Training" description="Train a new SoH classification model." />
        <LoadingSkeleton variant="card" />
      </div>
    )
  }

  if (datasetsQuery.isError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Training" />
        <ErrorState error={datasetsQuery.error} onRetry={() => datasetsQuery.refetch()} />
      </div>
    )
  }

  const datasets = datasetsQuery.data ?? []

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="Training" description="Train a new SoH classification model." />

      <TrainingConfigPanel
        datasets={datasets}
        isSubmitting={createRun.isPending}
        serverError={createRun.isError ? describeError(createRun.error) : null}
        onSubmit={(request) => {
          createRun.mutate(request, {
            onSuccess: (run) => setActiveRunId(run.id),
          })
        }}
      />

      {activeRunQuery.data && (
        <div className="flex flex-col gap-md">
          <h2 className="text-lg font-semibold text-text-primary">Current run</h2>
          <TrainingProgress run={activeRunQuery.data} />
          {activeRunQuery.data.status === 'completed' && (
            <div>
              <Button variant="secondary" onClick={() => navigate('/ds/experiments')}>
                View in Experiments
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Could not start training. Please try again.'
}
