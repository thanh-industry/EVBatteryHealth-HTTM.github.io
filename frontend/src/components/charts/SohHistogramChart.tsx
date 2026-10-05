import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { SohHistogramBin } from '../../types/api'
import { ChartFrame } from './ChartFrame'

export interface SohHistogramChartProps {
  bins: SohHistogramBin[]
}

export function SohHistogramChart({ bins }: SohHistogramChartProps) {
  const total = bins.reduce((sum, b) => sum + b.count, 0)

  if (bins.length === 0 || total === 0) {
    return (
      <ChartFrame
        title="SoH Distribution"
        ariaSummary="No State of Health histogram data available"
        isEmpty
        emptyMessage="No labelled rows available yet."
      />
    )
  }

  const data = bins.map((b) => ({
    ...b,
    label: `${b.bin_start.toFixed(0)}-${b.bin_end.toFixed(0)}`,
  }))

  const ariaSummary = `Histogram of State of Health percentage across ${data.length} bins from ${bins[0].bin_start.toFixed(0)}% to ${bins[bins.length - 1].bin_end.toFixed(0)}%, total ${total} rows`

  return (
    <ChartFrame title="SoH Distribution" unitNote="State of Health (%) - row count per band" ariaSummary={ariaSummary} isEmpty={false}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 20 }}>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            stroke="var(--color-text-secondary)"
            fontSize={11}
            label={{ value: 'State of Health (%)', position: 'insideBottom', offset: -12, style: { fill: 'var(--color-text-secondary)', fontSize: 12 } }}
          />
          <YAxis
            allowDecimals={false}
            stroke="var(--color-text-secondary)"
            fontSize={12}
            label={{ value: 'Row count', angle: -90, position: 'insideLeft', style: { fill: 'var(--color-text-secondary)', fontSize: 12 } }}
          />
          <Tooltip formatter={(value: number) => [`${value}`, 'Rows']} />
          <Bar dataKey="count" fill="var(--chart-seq-2)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
