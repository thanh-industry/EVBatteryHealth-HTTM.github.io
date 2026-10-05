import { cx } from '../../lib/utils'

export interface TabItem {
  id: string
  label: string
  disabled?: boolean
}

export interface TabsProps {
  tabs: TabItem[]
  activeId: string
  onChange: (id: string) => void
  'aria-label': string
}

export function Tabs({ tabs, activeId, onChange, ...rest }: TabsProps) {
  return (
    <div role="tablist" aria-label={rest['aria-label']} className="flex gap-md border-b border-border">
      {tabs.map((tab) => {
        const selected = tab.id === activeId
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={selected}
            disabled={tab.disabled}
            onClick={() => onChange(tab.id)}
            className={cx(
              'min-h-[44px] border-b-2 px-xl text-sm font-medium transition-colors duration-200',
              selected
                ? 'border-primary text-primary'
                : 'border-transparent text-text-secondary hover:text-text-primary',
              tab.disabled && 'cursor-not-allowed opacity-50',
            )}
          >
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
