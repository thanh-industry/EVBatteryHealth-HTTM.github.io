import type { LucideIcon } from 'lucide-react'
import { cx } from '../../lib/utils'

export interface KpiCardProps {
  label: string
  value: string
  unit?: string
  icon?: LucideIcon
  hint?: string
  tone?: 'neutral' | 'good' | 'monitor' | 'critical'
}

const TONE_ICON_CLASSES: Record<NonNullable<KpiCardProps['tone']>, string> = {
  neutral: 'text-primary',
  good: 'text-good',
  monitor: 'text-monitor',
  critical: 'text-critical',
}

export function KpiCard({ label, value, unit, icon: Icon, hint, tone = 'neutral' }: KpiCardProps) {
  return (
    <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
      <div className="flex items-center justify-between gap-md">
        <span className="text-sm font-semibold uppercase tracking-wide text-text-secondary">{label}</span>
        {Icon && <Icon className={cx('h-5 w-5', TONE_ICON_CLASSES[tone])} aria-hidden="true" />}
      </div>
      <div className="mt-sm flex items-baseline gap-sm">
        <span className="font-mono text-2xl font-semibold tabular-nums text-text-primary">{value}</span>
        {unit && <span className="text-sm text-text-muted">{unit}</span>}
      </div>
      {hint && <p className="mt-sm text-caption text-text-muted">{hint}</p>}
    </div>
  )
}
