import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ClassDistributionEntry, HealthClass } from '../../types/api'
import { HEALTH_META } from '../../lib/health'
import { STATUS_COLORS } from '../../lib/chartColors'
import { ChartFrame } from './ChartFrame'

export interface ClassDistributionChartProps {
  distribution: ClassDistributionEntry[]
}

const ORDER: HealthClass[] = ['GOOD', 'MONITOR', 'CRITICAL']

/**
 * "How are the 3 classes distributed?" -> bar (not pie), using the status
 * colors, since the classes ARE statuses (the one sanctioned palette
 * overlap, DESIGN_SYSTEM.md section 1).
 */
export function ClassDistributionChart({ distribution }: ClassDistributionChartProps) {
  const total = distribution.reduce((sum, d) => sum + d.count, 0)

  if (distribution.length === 0 || total === 0) {
    return (
      <ChartFrame
        title="Class Distribution"
        ariaSummary="No class distribution data available"
        isEmpty
        emptyMessage="No labelled rows available yet."
      />
    )
  }

  const data = ORDER.map((cls) => {
    const entry = distribution.find((d) => d.class === cls)
    return { class: cls, label: HEALTH_META[cls].label, count: entry?.count ?? 0 }
  })

  const ariaSummary = data.map((d) => `${d.label}: ${d.count}`).join(', ')

  return (
    <ChartFrame title="Class Distribution" unitNote="Number of batteries per health class" ariaSummary={ariaSummary} isEmpty={false}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 24, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" stroke="var(--color-text-secondary)" fontSize={12} />
          <YAxis
            allowDecimals={false}
            stroke="var(--color-text-secondary)"
            fontSize={12}
            label={{ value: 'Battery count', angle: -90, position: 'insideLeft', style: { fill: 'var(--color-text-secondary)', fontSize: 12 } }}
          />
          <Tooltip formatter={(value: number) => [`${value}`, 'Count']} />
          <Bar dataKey="count" isAnimationActive={false}>
            {data.map((entry) => (
              <Cell key={entry.class} fill={STATUS_COLORS[entry.class]} />
            ))}
            <LabelList dataKey="count" position="top" style={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
