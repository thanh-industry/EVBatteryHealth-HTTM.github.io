import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { MissingByColumnEntry } from '../../types/api'
import { SEQUENTIAL_COLORS } from '../../lib/chartColors'
import { ChartFrame } from './ChartFrame'

export interface MissingByColumnChartProps {
  columns: MissingByColumnEntry[]
  topN?: number
}

/**
 * "Which columns have missing data?" -> horizontal bar, top N, sequential
 * fill by magnitude (DESIGN_SYSTEM.md section 5).
 */
export function MissingByColumnChart({ columns, topN = 10 }: MissingByColumnChartProps) {
  const withMissing = columns.filter((c) => c.missing > 0)

  if (withMissing.length === 0) {
    return (
      <ChartFrame
        title="Missing Data by Column"
        ariaSummary="No missing data in this dataset"
        isEmpty
        emptyMessage="No missing values detected."
      />
    )
  }

  const data = [...withMissing]
    .sort((a, b) => b.missing_pct - a.missing_pct)
    .slice(0, topN)
    .map((c) => ({ ...c, missing_pct: Number(c.missing_pct.toFixed(2)) }))
    .reverse()

  const maxPct = Math.max(...data.map((d) => d.missing_pct), 1)
  const colorFor = (pct: number) => {
    const step = Math.min(3, Math.floor((pct / maxPct) * 4))
    return SEQUENTIAL_COLORS[step]
  }

  const ariaSummary = `Horizontal bar chart of the ${data.length} columns with the most missing data, ranging from ${data[0].missing_pct}% to ${data[data.length - 1].missing_pct}% missing`

  return (
    <ChartFrame
      title="Missing Data by Column"
      unitNote={`Top ${data.length} columns by missing percentage`}
      ariaSummary={ariaSummary}
      isEmpty={false}
      height={Math.max(260, data.length * 32)}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 32, left: 8, bottom: 8 }}
        >
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            stroke="var(--color-text-secondary)"
            fontSize={12}
            label={{ value: 'Missing (%)', position: 'insideBottom', offset: -4, style: { fill: 'var(--color-text-secondary)', fontSize: 12 } }}
          />
          <YAxis type="category" dataKey="column" stroke="var(--color-text-secondary)" fontSize={12} width={160} />
          <Tooltip formatter={(value: number) => [`${value}%`, 'Missing']} />
          <Bar dataKey="missing_pct" isAnimationActive={false}>
            {data.map((entry) => (
              <Cell key={entry.column} fill={colorFor(entry.missing_pct)} />
            ))}
            <LabelList dataKey="missing_pct" position="right" formatter={(v: number) => `${v}%`} style={{ fill: 'var(--color-text-secondary)', fontSize: 11 }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
