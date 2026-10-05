import { HelpCircle } from 'lucide-react'
import type { HealthClass } from '../../types/api'
import { getHealthMeta } from '../../lib/health'
import { cx } from '../../lib/utils'

export interface HealthStatusBadgeProps {
  healthClass: HealthClass | null | undefined
  size?: 'sm' | 'md'
  className?: string
}

/**
 * Renders a health classification as icon + text + color, never color
 * alone. This is both an accessibility requirement and an explicit
 * product requirement (see DESIGN_SYSTEM.md section 1).
 */
export function HealthStatusBadge({ healthClass, size = 'md', className }: HealthStatusBadgeProps) {
  const meta = getHealthMeta(healthClass)
  const iconSize = size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4'
  const textSize = size === 'sm' ? 'text-caption' : 'text-sm'

  if (!meta) {
    return (
      <span
        className={cx(
          'inline-flex items-center gap-sm rounded-full bg-muted px-lg py-xs font-medium text-text-muted',
          textSize,
          className,
        )}
      >
        <HelpCircle className={iconSize} aria-hidden="true" />
        Unknown
      </span>
    )
  }

  const Icon = meta.Icon
  return (
    <span
      className={cx(
        'inline-flex items-center gap-sm rounded-full px-lg py-xs font-medium',
        meta.bgClass,
        meta.textClass,
        textSize,
        className,
      )}
    >
      <Icon className={iconSize} aria-hidden="true" />
      {meta.label}
    </span>
  )
}
