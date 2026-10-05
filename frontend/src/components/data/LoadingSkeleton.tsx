import { cx } from '../../lib/utils'

export interface LoadingSkeletonProps {
  variant?: 'text' | 'card' | 'table' | 'chart'
  rows?: number
  className?: string
}

function Shimmer({ className }: { className?: string }) {
  return <div className={cx('animate-pulse rounded-md bg-muted', className)} aria-hidden="true" />
}

export function LoadingSkeleton({ variant = 'text', rows = 3, className }: LoadingSkeletonProps) {
  if (variant === 'card') {
    return (
      <div className={cx('rounded-lg border border-border bg-surface p-xl shadow-sm', className)} role="status" aria-label="Loading">
        <Shimmer className="h-sm w-24" />
        <Shimmer className="mt-lg h-xl w-32" />
        <Shimmer className="mt-md h-sm w-20" />
      </div>
    )
  }

  if (variant === 'table') {
    return (
      <div className={cx('rounded-lg border border-border bg-surface p-xl shadow-sm', className)} role="status" aria-label="Loading table">
        <Shimmer className="h-xl w-full" />
        <div className="mt-lg flex flex-col gap-md">
          {Array.from({ length: rows }).map((_, i) => (
            <Shimmer key={i} className="h-xl w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (variant === 'chart') {
    return (
      <div className={cx('rounded-lg border border-border bg-surface p-xl shadow-sm', className)} role="status" aria-label="Loading chart">
        <Shimmer className="h-sm w-32" />
        <Shimmer className="mt-lg h-[220px] w-full" />
      </div>
    )
  }

  return (
    <div className={cx('flex flex-col gap-md', className)} role="status" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Shimmer key={i} className="h-xl w-full" />
      ))}
    </div>
  )
}
