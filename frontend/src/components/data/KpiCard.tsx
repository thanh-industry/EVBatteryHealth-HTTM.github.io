import type { LucideIcon } from 'lucide-react'
import { cx } from '../../lib/utils'

export interface KpiCardProps {
  label: string
  value: string
  unit?: string
  icon?: LucideIcon
  hint?: string
  tone?: 'neutral' | 'good' | 'monitor' | 'critical'
  /**
   * 'metric' (default) uses the 32px Fira Code numeric-KPI treatment from
   * DESIGN_SYSTEM.md section 2 - reserved for actual metrics (percentages,
   * counts, scores). 'text' renders a single-line section-heading-sized
   * value for non-numeric content (dates, statuses) so it never wraps to
   * multiple lines and stretches the whole KPI row.
   */
  valueVariant?: 'metric' | 'text'
}

const TONE_ICON_CLASSES: Record<NonNullable<KpiCardProps['tone']>, string> = {
  neutral: 'text-primary',
  good: 'text-good',
  monitor: 'text-monitor',
  critical: 'text-critical',
}

export function KpiCard({ label, value, unit, icon: Icon, hint, tone = 'neutral', valueVariant = 'metric' }: KpiCardProps) {
  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-surface p-xl shadow-sm">
      <div className="flex items-center justify-between gap-md">
        <span className="text-sm font-semibold uppercase tracking-wide text-text-secondary">{label}</span>
        {Icon && <Icon className={cx('h-5 w-5 shrink-0', TONE_ICON_CLASSES[tone])} aria-hidden="true" />}
      </div>
      <div className="mt-sm flex items-baseline gap-sm">
        <span
          title={valueVariant === 'text' ? value : undefined}
          className={cx(
            'truncate text-text-primary',
            valueVariant === 'metric'
              ? 'font-mono text-2xl font-semibold tabular-nums'
              : 'text-lg font-semibold',
          )}
        >
          {value}
        </span>
        {unit && <span className="text-sm text-text-muted">{unit}</span>}
      </div>
      {hint && <p className="mt-sm text-caption text-text-muted">{hint}</p>}
    </div>
  )
}
