import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Measurement } from '../../types/api'
import { formatDate } from '../../lib/utils'
import { ChartFrame } from './ChartFrame'
import { SohGauge } from './SohGauge'
import { classifySoh } from '../../lib/health'
import type { Thresholds } from '../../types/api'

export interface TrendChartProps {
  measurements: Measurement[]
  thresholds?: Thresholds | null
}

interface TooltipPayloadItem {
  value: number
  payload: { recorded_at: string }
}

function TrendTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) {
  if (!active || !payload?.length) return null
  const point = payload[0]
  return (
    <div className="rounded-md border border-border bg-surface p-md shadow-md">
      <p className="text-caption text-text-muted">{formatDate(point.payload.recorded_at)}</p>
      <p className="font-mono text-sm font-semibold text-text-primary">{point.value.toFixed(1)}% SoH</p>
    </div>
  )
}

/**
 * "How has this battery's SoH changed?" -> line chart, >= 4 points.
 * Fewer than 4 points falls back to a stat tile (DESIGN_SYSTEM.md section 5).
 */
export function TrendChart({ measurements, thresholds }: TrendChartProps) {
  const sorted = [...measurements].sort(
    (a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime(),
  )

  if (sorted.length === 0) {
    return (
      <ChartFrame
        title="SoH Trend"
        ariaSummary="No SoH history available"
        isEmpty
        emptyMessage="No SoH history recorded yet."
      />
    )
  }

  if (sorted.length < 4) {
    const latest = sorted[sorted.length - 1]
    const healthClass = classifySoh(latest.soh, thresholds)
    return (
      <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
        <h3 className="mb-lg text-sm font-semibold text-text-primary">SoH Trend</h3>
        <p className="mb-lg text-caption text-text-muted">
          Not enough readings yet for a trend line (need at least 4). Showing the latest reading.
        </p>
        <SohGauge soh={latest.soh} healthClass={healthClass} />
      </div>
    )
  }

  const ariaSummary = `Line chart of State of Health percentage over time, from ${sorted[0].soh.toFixed(1)}% on ${formatDate(sorted[0].recorded_at)} to ${sorted[sorted.length - 1].soh.toFixed(1)}% on ${formatDate(sorted[sorted.length - 1].recorded_at)}`

  return (
    <ChartFrame title="SoH Trend" unitNote="State of Health (%) over time" ariaSummary={ariaSummary} isEmpty={false}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sorted} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="recorded_at"
            tickFormatter={(value: string) => formatDate(value)}
            stroke="var(--color-text-secondary)"
            fontSize={12}
          />
          <YAxis
            domain={[0, 100]}
            tickCount={6}
            stroke="var(--color-text-secondary)"
            fontSize={12}
            label={{ value: 'State of Health (%)', angle: -90, position: 'insideLeft', style: { fill: 'var(--color-text-secondary)', fontSize: 12 } }}
          />
          <Tooltip content={<TrendTooltip />} />
          <Line
            type="monotone"
            dataKey="soh"
            name="State of Health (%)"
            stroke="var(--chart-seq-3)"
            strokeWidth={2}
            dot={{ r: 3 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
