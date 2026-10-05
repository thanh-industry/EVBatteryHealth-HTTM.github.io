import type { HTMLAttributes, ReactNode } from 'react'
import { cx } from '../../lib/utils'

export interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  title?: ReactNode
  actions?: ReactNode
  padded?: boolean
}

export function Card({ title, actions, padded = true, className, children, ...rest }: CardProps) {
  return (
    <div
      className={cx(
        'rounded-lg border border-border bg-surface shadow-sm',
        padded && 'p-xl',
        className,
      )}
      {...rest}
    >
      {(title || actions) && (
        <div className="mb-lg flex items-center justify-between gap-md">
          {title && <h3 className="text-sm font-semibold uppercase tracking-wide text-text-secondary">{title}</h3>}
          {actions}
        </div>
      )}
      {children}
    </div>
  )
}
