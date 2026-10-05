import type { ReactNode } from 'react'
import { EmptyState } from '../data/EmptyState'

export interface ChartFrameProps {
  title: string
  unitNote?: string
  ariaSummary: string
  isEmpty: boolean
  emptyMessage?: string
  children?: ReactNode
  legend?: ReactNode
  height?: number
}

/**
 * Shared chart shell: title, optional unit note, an aria-label summary for
 * screen readers (DESIGN_SYSTEM.md section 5), a legend slot, and the
 * mandatory empty state. Every chart in the app renders through this.
 */
export function ChartFrame({
  title,
  unitNote,
  ariaSummary,
  isEmpty,
  emptyMessage = 'No data available yet.',
  children,
  legend,
  height = 260,
}: ChartFrameProps) {
  return (
    <div className="rounded-lg border border-border bg-surface p-xl shadow-sm">
      <div className="mb-lg flex items-start justify-between gap-md">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
          {unitNote && <p className="text-caption text-text-muted">{unitNote}</p>}
        </div>
        {legend}
      </div>
      {isEmpty ? (
        <EmptyState title={emptyMessage} />
      ) : (
        <div role="img" aria-label={ariaSummary} style={{ height }}>
          {children}
        </div>
      )}
    </div>
  )
}
