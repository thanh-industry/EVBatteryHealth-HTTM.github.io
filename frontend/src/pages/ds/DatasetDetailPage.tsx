import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { Tabs } from '../../components/ui/Tabs'
import { Button } from '../../components/ui/Button'
import { useDataset } from '../../hooks/useDatasets'
import { formatDateTime, formatPercent } from '../../lib/utils'
import { DatasetPreviewTab } from './dataset-detail/DatasetPreviewTab'
import { DatasetQualityTab } from './dataset-detail/DatasetQualityTab'

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const datasetId = id ? Number(id) : undefined
  const [activeTab, setActiveTab] = useState<'preview' | 'quality'>('preview')

  const datasetQuery = useDataset(datasetId)

  if (!datasetId || Number.isNaN(datasetId)) {
    return <ErrorState error={new Error('Invalid dataset id.')} />
  }

  if (datasetQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="table" rows={6} />
      </div>
    )
  }

  if (datasetQuery.isError) {
    return <ErrorState error={datasetQuery.error} onRetry={() => datasetQuery.refetch()} />
  }

  const dataset = datasetQuery.data
  if (!dataset) return null

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader
        title={dataset.name}
        description={`${dataset.filename} - uploaded ${formatDateTime(dataset.uploaded_at)}`}
        actions={<Button variant="secondary" onClick={() => navigate('/ds/datasets')}>Back to datasets</Button>}
      />

      <dl className="grid grid-cols-2 gap-md sm:grid-cols-4">
        <Stat label="Rows" value={dataset.row_count.toLocaleString()} />
        <Stat label="Columns" value={String(dataset.column_count)} />
        <Stat label="Missing cells" value={`${dataset.missing_cells.toLocaleString()} (${formatPercent(dataset.missing_pct)})`} />
        <Stat label="Duplicate rows" value={String(dataset.duplicate_rows)} />
      </dl>

      {dataset.status === 'invalid' && dataset.message && (
        <p role="alert" className="rounded-md border border-critical bg-critical-bg p-lg text-sm text-critical">
          {dataset.message}
        </p>
      )}

      <Tabs
        aria-label="Dataset detail sections"
        tabs={[
          { id: 'preview', label: 'Preview' },
          { id: 'quality', label: 'Data Quality' },
        ]}
        activeId={activeTab}
        onChange={(id) => setActiveTab(id as 'preview' | 'quality')}
      />

      {activeTab === 'preview' ? (
        <DatasetPreviewTab datasetId={dataset.id} />
      ) : (
        <DatasetQualityTab datasetId={dataset.id} />
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-lg shadow-sm">
      <dt className="text-caption text-text-muted">{label}</dt>
      <dd className="font-mono text-base font-semibold tabular-nums text-text-primary">{value}</dd>
    </div>
  )
}
