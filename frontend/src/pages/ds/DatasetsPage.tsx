import { Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ConfirmDialog } from '../../components/ui/ConfirmDialog'
import { CsvUploader } from '../../components/data/CsvUploader'
import { DataTable, type DataTableColumn } from '../../components/data/DataTable'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { useDatasets, useDeleteDataset, useUploadDataset } from '../../hooks/useDatasets'
import { ApiError } from '../../lib/api'
import { formatDateTime, formatPercent } from '../../lib/utils'
import type { Dataset } from '../../types/api'

export function DatasetsPage() {
  const navigate = useNavigate()
  const datasetsQuery = useDatasets()
  const uploadMutation = useUploadDataset()
  const deleteMutation = useDeleteDataset()
  const [pendingDelete, setPendingDelete] = useState<Dataset | null>(null)

  if (datasetsQuery.isLoading) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Datasets" description="Upload and manage training datasets." />
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="table" rows={4} />
      </div>
    )
  }

  if (datasetsQuery.isError) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Datasets" />
        <ErrorState error={datasetsQuery.error} onRetry={() => datasetsQuery.refetch()} />
      </div>
    )
  }

  const datasets = datasetsQuery.data ?? []

  const columns: DataTableColumn<Dataset>[] = [
    { key: 'name', header: 'Name', accessor: (d) => d.name, sortable: true },
    {
      key: 'row_count',
      header: 'Rows',
      accessor: (d) => d.row_count,
      sortable: true,
      numeric: true,
      align: 'right',
      render: (d) => d.row_count.toLocaleString(),
    },
    { key: 'column_count', header: 'Columns', accessor: (d) => d.column_count, sortable: true, numeric: true, align: 'right' },
    {
      key: 'missing_pct',
      header: 'Missing',
      accessor: (d) => d.missing_pct,
      sortable: true,
      numeric: true,
      align: 'right',
      render: (d) => formatPercent(d.missing_pct),
    },
    { key: 'duplicate_rows', header: 'Duplicates', accessor: (d) => d.duplicate_rows, sortable: true, numeric: true, align: 'right' },
    {
      key: 'status',
      header: 'Status',
      accessor: (d) => d.status,
      sortable: true,
      render: (d) => (
        <Badge tone={d.status === 'ready' ? 'good' : 'critical'}>{d.status}</Badge>
      ),
    },
    { key: 'uploaded_at', header: 'Uploaded', accessor: (d) => d.uploaded_at, sortable: true, render: (d) => formatDateTime(d.uploaded_at) },
    {
      key: 'actions',
      header: 'Actions',
      render: (d) => (
        <div className="flex items-center gap-md">
          <Button variant="secondary" size="sm" onClick={() => navigate(`/ds/datasets/${d.id}`)}>
            View
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPendingDelete(d)}
            aria-label={`Delete dataset ${d.name}`}
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="Datasets" description="Upload and manage training datasets." />

      <CsvUploader
        onUpload={(file) => uploadMutation.mutate(file)}
        isUploading={uploadMutation.isPending}
        serverError={uploadMutation.isError ? describeUploadError(uploadMutation.error) : null}
      />

      <DataTable
        caption="Uploaded datasets"
        columns={columns}
        rows={datasets}
        getRowId={(d) => d.id}
        emptyTitle="No datasets uploaded yet"
        emptyDescription="Drag a CSV file into the box above to get started."
      />

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete dataset"
        description={
          pendingDelete
            ? `Delete "${pendingDelete.name}"? This cannot be undone and any training runs that used it will keep their results.`
            : ''
        }
        confirmLabel="Delete"
        loading={deleteMutation.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (!pendingDelete) return
          deleteMutation.mutate(pendingDelete.id, {
            onSuccess: () => setPendingDelete(null),
          })
        }}
      />
    </div>
  )
}

function describeUploadError(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Upload failed. Please try again.'
}
