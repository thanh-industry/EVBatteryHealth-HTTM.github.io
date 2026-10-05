import type { ReactNode } from 'react'

export interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="mb-xl flex flex-wrap items-start justify-between gap-lg">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">{title}</h1>
        {description && <p className="mt-sm text-sm text-text-secondary">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-md">{actions}</div>}
    </div>
  )
}
