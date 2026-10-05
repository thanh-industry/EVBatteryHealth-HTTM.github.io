import { Bar, BarChart, CartesianGrid, Legend, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Algorithm, Metrics } from '../../types/api'
import { ALGORITHM_LABELS, CATEGORICAL_COLORS } from '../../lib/chartColors'
import { ChartFrame } from './ChartFrame'

export interface AlgorithmMetrics {
  algorithm: Algorithm
  metrics: Metrics
}

export interface MetricComparisonChartProps {
  entries: AlgorithmMetrics[]
}

const METRIC_DEFS: { key: keyof Metrics; label: string }[] = [
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'precision_macro', label: 'Precision' },
  { key: 'recall_macro', label: 'Recall' },
  { key: 'f1_macro', label: 'F1' },
]

interface ChartRow {
  metric: string
  [algorithm: string]: string | number
}

/**
 * "Which model performs best?" -> grouped bar, metrics on x, algorithms as
 * series. Accuracy/Precision/Recall/F1 are shown together - never a single
 * winner declared on accuracy alone (DESIGN_SYSTEM.md + ARCHITECTURE.md).
 * All values come straight from Metrics objects returned by the API.
 */
export function MetricComparisonChart({ entries }: MetricComparisonChartProps) {
  if (entries.length === 0) {
    return (
      <ChartFrame
        title="Model Comparison"
        ariaSummary="No trained models to compare yet"
        isEmpty
        emptyMessage="Train at least one model to see a comparison."
      />
    )
  }

  const data: ChartRow[] = METRIC_DEFS.map(({ key, label }) => {
    const row: ChartRow = { metric: label }
    entries.forEach((entry) => {
      row[entry.algorithm] = Number((entry.metrics[key] as number) * 100)
    })
    return row
  })

  const ariaSummary = `Grouped bar chart comparing ${entries.map((e) => ALGORITHM_LABELS[e.algorithm] ?? e.algorithm).join(', ')} across accuracy, precision, recall and F1 score, each as a percentage from 0 to 100`

  return (
    <ChartFrame
      title="Model Comparison"
      unitNote="Score (%) - higher is better for all four metrics"
      ariaSummary={ariaSummary}
      isEmpty={false}
      height={320}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 24, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="metric" stroke="var(--color-text-secondary)" fontSize={12} />
          <YAxis
            domain={[0, 100]}
            stroke="var(--color-text-secondary)"
            fontSize={12}
            label={{ value: 'Score (%)', angle: -90, position: 'insideLeft', style: { fill: 'var(--color-text-secondary)', fontSize: 12 } }}
          />
          <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
          <Legend formatter={(value: string) => ALGORITHM_LABELS[value] ?? value} />
          {entries.map((entry, index) => (
            <Bar
              key={entry.algorithm}
              dataKey={entry.algorithm}
              name={ALGORITHM_LABELS[entry.algorithm] ?? entry.algorithm}
              fill={CATEGORICAL_COLORS[index % CATEGORICAL_COLORS.length]}
              isAnimationActive={false}
            >
              <LabelList
                dataKey={entry.algorithm}
                position="top"
                formatter={(value: number) => `${value.toFixed(1)}`}
                style={{ fill: 'var(--color-text-secondary)', fontSize: 11 }}
              />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
