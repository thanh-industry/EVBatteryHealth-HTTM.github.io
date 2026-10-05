import { RadialBar, RadialBarChart, PolarAngleAxis } from 'recharts'
import type { HealthClass } from '../../types/api'
import { HealthStatusBadge } from '../data/HealthStatusBadge'
import { STATUS_COLORS } from '../../lib/chartColors'
import { getHealthMeta } from '../../lib/health'

export interface SohGaugeProps {
  soh: number | null
  healthClass: HealthClass | null
  size?: number
}

/**
 * Single-KPI-with-emphasis gauge for the current SoH reading. Fixed
 * 0-100 domain (never auto-scaled) per DESIGN_SYSTEM.md section 5.
 * Color is always paired with the numeric value and a text+icon badge -
 * never color alone.
 */
export function SohGauge({ soh, healthClass, size = 180 }: SohGaugeProps) {
  const meta = getHealthMeta(healthClass)
  const color = healthClass ? STATUS_COLORS[healthClass] : 'var(--color-text-muted)'
  const value = soh ?? 0
  const label = soh === null || soh === undefined ? 'No reading available' : `${soh.toFixed(1)} percent, classified as ${meta?.label ?? 'unknown'}`

  return (
    <div className="flex flex-col items-center gap-md">
      <div role="img" aria-label={`State of Health: ${label}`} style={{ width: size, height: size, position: 'relative' }}>
        <RadialBarChart
          width={size}
          height={size}
          cx="50%"
          cy="50%"
          innerRadius="72%"
          outerRadius="100%"
          barSize={14}
          data={[{ value }]}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: 'var(--color-muted)' }} dataKey="value" cornerRadius={8} fill={color} isAnimationActive={false} />
        </RadialBarChart>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono text-2xl font-semibold tabular-nums text-text-primary">
            {soh === null || soh === undefined ? '--' : soh.toFixed(1)}
          </span>
          <span className="text-caption text-text-muted">% SoH</span>
        </div>
      </div>
      <p className="text-caption text-text-muted">State of Health (%)</p>
      <HealthStatusBadge healthClass={healthClass} />
    </div>
  )
}
