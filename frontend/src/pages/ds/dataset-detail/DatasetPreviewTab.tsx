import { ErrorState } from '../../../components/data/ErrorState'
import { LoadingSkeleton } from '../../../components/data/LoadingSkeleton'
import { DataTable, type DataTableColumn } from '../../../components/data/DataTable'
import { useDatasetPreview } from '../../../hooks/useDatasets'

export function DatasetPreviewTab({ datasetId }: { datasetId: number }) {
  const previewQuery = useDatasetPreview(datasetId, 20)

  if (previewQuery.isLoading) return <LoadingSkeleton variant="table" rows={6} />
  if (previewQuery.isError) return <ErrorState error={previewQuery.error} onRetry={() => previewQuery.refetch()} />

  const preview = previewQuery.data
  if (!preview || preview.rows.length === 0) {
    return <p className="text-sm text-text-secondary">No preview rows available.</p>
  }

  const columns: DataTableColumn<Record<string, unknown>>[] = preview.columns.map((col) => ({
    key: col,
    header: col,
    accessor: (row) => {
      const value = row[col]
      return typeof value === 'number' ? value : value === null || value === undefined ? null : String(value)
    },
    numeric: typeof preview.rows[0]?.[col] === 'number',
  }))

  return (
    <div className="flex flex-col gap-md">
      <p className="text-caption text-text-muted">Showing first {preview.rows.length} rows of {preview.columns.length} columns.</p>
      <DataTable
        caption="Dataset preview"
        columns={columns}
        rows={preview.rows}
        getRowId={(_, index) => index}
      />
    </div>
  )
}
