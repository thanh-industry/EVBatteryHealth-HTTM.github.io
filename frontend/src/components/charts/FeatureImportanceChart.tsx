import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { FeatureImportanceEntry } from '../../types/api'
import { ChartFrame } from './ChartFrame'

export interface FeatureImportanceChartProps {
  features: FeatureImportanceEntry[]
  topN?: number
}

export function FeatureImportanceChart({ features, topN = 10 }: FeatureImportanceChartProps) {
  if (features.length === 0) {
    return (
      <ChartFrame
        title="Feature Importance"
        ariaSummary="No feature importance available for this model"
        isEmpty
        emptyMessage="Not available for this algorithm."
      />
    )
  }

  const data = [...features]
    .sort((a, b) => b.importance - a.importance)
    .slice(0, topN)
    .reverse()

  const ariaSummary = `Horizontal bar chart of the top ${data.length} most important features, led by ${data[data.length - 1].feature}`

  return (
    <ChartFrame
      title="Feature Importance"
      unitNote={`Top ${data.length} features`}
      ariaSummary={ariaSummary}
      isEmpty={false}
      height={Math.max(260, data.length * 32)}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" stroke="var(--color-text-secondary)" fontSize={12} label={{ value: 'Importance', position: 'insideBottom', offset: -4, style: { fill: 'var(--color-text-secondary)', fontSize: 12 } }} />
          <YAxis type="category" dataKey="feature" stroke="var(--color-text-secondary)" fontSize={12} width={160} />
          <Tooltip formatter={(value: number) => [value.toFixed(4), 'Importance']} />
          <Bar dataKey="importance" fill="var(--chart-seq-3)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
