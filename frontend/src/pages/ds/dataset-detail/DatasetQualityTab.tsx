import { AlertTriangle } from 'lucide-react'
import { ErrorState } from '../../../components/data/ErrorState'
import { LoadingSkeleton } from '../../../components/data/LoadingSkeleton'
import { ClassDistributionChart } from '../../../components/charts/ClassDistributionChart'
import { SohHistogramChart } from '../../../components/charts/SohHistogramChart'
import { MissingByColumnChart } from '../../../components/charts/MissingByColumnChart'
import { useDatasetQuality } from '../../../hooks/useDatasets'

export function DatasetQualityTab({ datasetId }: { datasetId: number }) {
  const qualityQuery = useDatasetQuality(datasetId)

  if (qualityQuery.isLoading) {
    return (
      <div className="grid grid-cols-1 gap-lg lg:grid-cols-2">
        <LoadingSkeleton variant="chart" />
        <LoadingSkeleton variant="chart" />
      </div>
    )
  }

  if (qualityQuery.isError) {
    return <ErrorState error={qualityQuery.error} onRetry={() => qualityQuery.refetch()} />
  }

  const quality = qualityQuery.data
  if (!quality) return null

  return (
    <div className="flex flex-col gap-xl">
      <dl className="grid grid-cols-2 gap-md sm:grid-cols-4">
        <Stat label="Labelled rows" value={quality.labelled_rows} />
        <Stat label="Dropped (no label)" value={quality.dropped_missing_label} />
        <Stat label="Duplicate rows" value={quality.duplicate_rows} />
        <Stat label="Total rows" value={quality.row_count} />
      </dl>

      <div className="grid grid-cols-1 gap-lg lg:grid-cols-2">
        <ClassDistributionChart distribution={quality.class_distribution} />
        <SohHistogramChart bins={quality.soh_histogram} />
      </div>

      <MissingByColumnChart columns={quality.missing_by_column} />

      <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
        <div className="mb-lg flex items-center gap-md">
          <AlertTriangle className="h-5 w-5 text-monitor" aria-hidden="true" />
          <h3 className="text-sm font-semibold text-text-primary">Excluded columns (leakage blocklist)</h3>
        </div>
        {quality.excluded_columns.length === 0 ? (
          <p className="text-sm text-text-secondary">No columns were excluded for this dataset.</p>
        ) : (
          <ul className="flex flex-col gap-md">
            {quality.excluded_columns.map((col) => (
              <li key={col.column} className="border-b border-border pb-md last:border-0 last:pb-0">
                <p className="font-mono text-sm font-semibold text-text-primary">{col.column}</p>
                <p className="text-sm text-text-secondary">{col.reason}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-caption text-text-muted">{label}</dt>
      <dd className="font-mono text-base font-semibold tabular-nums text-text-primary">{value.toLocaleString()}</dd>
    </div>
  )
}
