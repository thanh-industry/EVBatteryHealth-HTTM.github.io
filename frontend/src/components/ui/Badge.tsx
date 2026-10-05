import type { HTMLAttributes } from 'react'
import { cx } from '../../lib/utils'

export type BadgeTone = 'neutral' | 'primary' | 'info' | 'good' | 'monitor' | 'critical'

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone
}

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: 'bg-muted text-text-secondary',
  primary: 'bg-primary text-on-primary',
  info: 'bg-surface text-info border border-info',
  good: 'bg-good-bg text-good',
  monitor: 'bg-monitor-bg text-monitor',
  critical: 'bg-critical-bg text-critical',
}

export function Badge({ tone = 'neutral', className, children, ...rest }: BadgeProps) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-sm rounded-full px-lg py-xs text-caption font-medium',
        TONE_CLASSES[tone],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  )
}
