import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ErrorState } from '../../components/data/ErrorState'
import { LoadingSkeleton } from '../../components/data/LoadingSkeleton'
import { HealthStatusBadge } from '../../components/data/HealthStatusBadge'
import { PageHeader } from '../../components/layout/PageHeader'
import { Button } from '../../components/ui/Button'
import { useDiagnosticsList } from '../../hooks/useDiagnostics'
import { STATUS_COLORS } from '../../lib/chartColors'
import { formatDateTime } from '../../lib/utils'
import type { Diagnostic } from '../../types/api'

interface LocationState {
  diagnostic?: Diagnostic
}

export function DiagnosticDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const stateDiagnostic = (location.state as LocationState | null)?.diagnostic

  // The API contract has no GET /api/diagnostics/{id}; when we did not
  // arrive here via navigation state (e.g. a page refresh), fall back to
  // the list endpoint and find the matching record client-side.
  const listQuery = useDiagnosticsList({ limit: 50 })
  const diagnostic = stateDiagnostic ?? listQuery.data?.find((d) => String(d.id) === id)

  if (!stateDiagnostic && listQuery.isLoading) {
    return <LoadingSkeleton variant="card" />
  }

  if (!stateDiagnostic && listQuery.isError) {
    return <ErrorState error={listQuery.error} onRetry={() => listQuery.refetch()} />
  }

  if (!diagnostic) {
    return (
      <div className="flex flex-col gap-xl">
        <PageHeader title="Diagnostic" />
        <ErrorState
          error={new Error('This diagnostic could not be found in the most recent 50 records.')}
          title="Diagnostic not found"
        />
      </div>
    )
  }

  const probData = diagnostic.class_probabilities?.map((p) => ({
    class: p.class,
    probability: Number((p.probability * 100).toFixed(1)),
  }))

  return (
    <div className="flex flex-col gap-xl">
      <PageHeader
        title={`Diagnostic - ${diagnostic.vehicle_code}`}
        description={formatDateTime(diagnostic.created_at)}
        actions={<Button variant="secondary" onClick={() => navigate('/tech/history')}>Back to history</Button>}
      />

      <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
        <div className="flex items-center gap-lg">
          <HealthStatusBadge healthClass={diagnostic.predicted_class} />
          <span className="font-mono text-2xl font-semibold tabular-nums text-text-primary">
            {diagnostic.soh.toFixed(1)}%
          </span>
          <span className="text-caption text-text-muted">SoH</span>
        </div>
        <p className="mt-lg text-sm text-text-secondary">{diagnostic.recommendation}</p>
        <dl className="mt-lg grid grid-cols-2 gap-md sm:grid-cols-4">
          <Field label="Confidence" value={diagnostic.confidence !== null ? `${(diagnostic.confidence * 100).toFixed(1)}%` : 'Not available'} />
          <Field label="Model" value={`${diagnostic.model_algorithm} ${diagnostic.model_version}`} />
          <Field label="Technician" value={diagnostic.technician_name ?? 'Unknown'} />
          <Field label="Battery" value={diagnostic.battery_serial} />
        </dl>
        {diagnostic.notes && (
          <p className="mt-lg border-t border-border pt-lg text-sm text-text-secondary">Notes: {diagnostic.notes}</p>
        )}
      </div>

      {probData && probData.length > 0 && (
        <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
          <h3 className="mb-lg text-sm font-semibold text-text-primary">Class probabilities</h3>
          <div
            role="img"
            aria-label={probData.map((p) => `${p.class}: ${p.probability}%`).join(', ')}
            style={{ height: 220 }}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={probData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="class" stroke="var(--color-text-secondary)" fontSize={12} />
                <YAxis
                  domain={[0, 100]}
                  stroke="var(--color-text-secondary)"
                  fontSize={12}
                  label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft', style: { fill: 'var(--color-text-secondary)', fontSize: 12 } }}
                />
                <Tooltip formatter={(value: number) => [`${value}%`, 'Probability']} />
                <Bar dataKey="probability" isAnimationActive={false}>
                  {probData.map((entry) => (
                    <Cell key={entry.class} fill={STATUS_COLORS[entry.class as keyof typeof STATUS_COLORS]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
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
      <dd className="text-sm font-semibold text-text-primary">{value}</dd>
    </div>
  )
}
