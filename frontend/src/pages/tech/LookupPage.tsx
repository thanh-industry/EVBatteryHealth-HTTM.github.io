import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ErrorState } from '../../components/data/ErrorState'
import { EmptyState } from '../../components/data/EmptyState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { PageHeader } from '../../components/layout/PageHeader'
import { BatterySummaryCard } from '../../components/battery/BatterySummaryCard'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { useBatteryLookup, useRunDiagnostic } from '../../hooks/useDiagnostics'
import { ApiError } from '../../lib/api'
import { formatDateTime } from '../../lib/utils'

export function LookupPage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [submittedCode, setSubmittedCode] = useState<string | undefined>(undefined)
  const [notes, setNotes] = useState('')

  const lookupQuery = useBatteryLookup(submittedCode)
  const runDiagnostic = useRunDiagnostic()

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = query.trim()
    if (trimmed) setSubmittedCode(trimmed)
  }

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader title="Lookup" description="Find a vehicle or battery by code to run a diagnostic." />

      <form onSubmit={handleSearch} className="flex flex-wrap items-end gap-md">
        <Input
          label="Vehicle code or battery serial"
          containerClassName="min-w-[240px] flex-1"
          placeholder="e.g. EV100042"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" disabled={!query.trim()}>
          Search
        </Button>
      </form>

      {!submittedCode && (
        <EmptyState title="Search for a vehicle or battery" description="Enter a vehicle code or battery serial above." />
      )}

      {submittedCode && lookupQuery.isLoading && <LoadingSkeleton variant="card" />}

      {submittedCode && lookupQuery.isError && (
        <ErrorState
          error={lookupQuery.error}
          title={lookupQuery.error instanceof ApiError && lookupQuery.error.status === 404 ? 'Not found' : 'Could not load this battery'}
          onRetry={() => lookupQuery.refetch()}
        />
      )}

      {submittedCode && lookupQuery.data && (
        <div className="flex flex-col gap-lg">
          <BatterySummaryCard vehicle={lookupQuery.data.vehicle} battery={lookupQuery.data.battery} />

          {lookupQuery.data.latest_measurement && (
            <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
              <h3 className="mb-md text-sm font-semibold text-text-primary">Latest measurement</h3>
              <dl className="grid grid-cols-2 gap-md sm:grid-cols-4">
                <Field label="Recorded" value={formatDateTime(lookupQuery.data.latest_measurement.recorded_at)} />
                <Field label="SoH" value={`${lookupQuery.data.latest_measurement.soh.toFixed(1)}%`} />
                <Field
                  label="Internal resistance"
                  value={lookupQuery.data.latest_measurement.internal_resistance?.toFixed(3) ?? '--'}
                />
                <Field
                  label="Cell temp (avg)"
                  value={lookupQuery.data.latest_measurement.cell_temperature_avg?.toFixed(1) ?? '--'}
                />
              </dl>
            </div>
          )}

          <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
            <h3 className="mb-md text-sm font-semibold text-text-primary">Run diagnostic</h3>
            <label htmlFor="diagnostic-notes" className="mb-sm block text-sm font-medium text-text-primary">
              Notes (optional)
            </label>
            <textarea
              id="diagnostic-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="mb-md w-full rounded-md border border-border-strong bg-surface p-lg text-base text-text-primary"
            />
            {runDiagnostic.isError && (
              <p role="alert" className="mb-md text-sm text-critical">
                {describeDiagnosticError(runDiagnostic.error)}
              </p>
            )}
            <Button
              loading={runDiagnostic.isPending}
              onClick={() => {
                runDiagnostic.mutate(
                  { code: submittedCode, notes: notes.trim() || undefined },
                  {
                    onSuccess: (diagnostic) =>
                      navigate(`/tech/diagnostics/${diagnostic.id}`, { state: { diagnostic } }),
                  },
                )
              }}
            >
              Run diagnostic
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-caption text-text-muted">{label}</dt>
      <dd className="font-mono text-sm font-semibold tabular-nums text-text-primary">{value}</dd>
    </div>
  )
}

function describeDiagnosticError(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return 'Could not run the diagnostic. Please try again.'
}
