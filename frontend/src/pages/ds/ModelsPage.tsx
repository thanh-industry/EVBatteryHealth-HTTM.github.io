import { useState } from 'react'
import { Boxes } from 'lucide-react'
import { EmptyState } from '../../components/data/EmptyState'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { ModelCard } from '../../components/models/ModelCard'
import { Button } from '../../components/ui/Button'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'
import { useActiveModel, useDeployModel, useDeployableModels } from '../../hooks/useModels'
import { ApiError } from '../../lib/api'
import type { TrainingRun } from '../../types/api'

export function ModelsPage() {
  const modelsQuery = useDeployableModels()
  const activeModelQuery = useActiveModel()
  const deployMutation = useDeployModel()
  const [pendingDeploy, setPendingDeploy] = useState<TrainingRun | null>(null)

  const isLoading = modelsQuery.isLoading || activeModelQuery.isLoading
  const firstError = modelsQuery.error ?? activeModelQuery.error

  if (isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Models" description="Deployable models and the one currently live." />
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="card" />
      </div>
    )
  }

  if (firstError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Models" />
        <ErrorState
          error={firstError}
          onRetry={() => {
            modelsQuery.refetch()
            activeModelQuery.refetch()
          }}
        />
      </div>
    )
  }

  const models = modelsQuery.data ?? []
  const activeModel = activeModelQuery.data ?? null

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="Models" description="Deployable models and the one currently live." />

      <div>
        <h2 className="mb-md text-lg font-semibold text-text-primary">Active deployment</h2>
        {activeModel ? (
          <ModelCard
            version={activeModel.version}
            algorithm={activeModel.algorithm}
            datasetName={activeModel.dataset_name}
            dateLabel="Deployed"
            dateValue={activeModel.deployed_at}
            metrics={activeModel.metrics}
            supportsProbability={activeModel.supports_probability}
            isActive
          />
        ) : (
          <EmptyState
            icon={Boxes}
            title="No model deployed"
            description="Deploy a completed training run below to serve diagnostics."
          />
        )}
      </div>

      <div>
        <h2 className="mb-md text-lg font-semibold text-text-primary">Deployable models</h2>
        {models.length === 0 ? (
          <EmptyState title="No completed training runs yet" description="Train a model first on the Training page." />
        ) : (
          <div className="flex flex-col gap-lg">
            {models.map((run) => (
              <ModelCard
                key={run.id}
                version={run.version}
                algorithm={run.algorithm}
                datasetName={run.dataset_name}
                dateLabel="Trained"
                dateValue={run.completed_at}
                metrics={run.metrics!}
                supportsProbability={run.supports_probability}
                isActive={run.is_deployed}
                actions={
                  <Button
                    variant={run.is_deployed ? 'secondary' : 'primary'}
                    disabled={run.is_deployed}
                    disabledReason={run.is_deployed ? 'This model is already deployed.' : undefined}
                    onClick={() => setPendingDeploy(run)}
                  >
                    {run.is_deployed ? 'Deployed' : 'Deploy'}
                  </Button>
                }
              />
            ))}
          </div>
        )}
      </div>

      {deployMutation.isError && (
        <p role="alert" className="text-sm text-critical">
          {describeError(deployMutation.error)}
        </p>
      )}

      <ConfirmDialog
        open={pendingDeploy !== null}
        title="Deploy model"
        description={
          pendingDeploy
            ? `Deploy ${pendingDeploy.version ?? `run #${pendingDeploy.id}`} (${pendingDeploy.algorithm})? This replaces the currently active model for all new diagnostics.`
            : ''
        }
        confirmLabel="Deploy"
        loading={deployMutation.isPending}
        onCancel={() => setPendingDeploy(null)}
        onConfirm={() => {
          if (!pendingDeploy) return
          deployMutation.mutate(pendingDeploy.id, {
            onSuccess: () => setPendingDeploy(null),
          })
        }}
      />
    </div>
  )
}

function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Could not deploy this model. Please try again.'
}
