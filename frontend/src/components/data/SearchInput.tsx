import { Search } from 'lucide-react'
import { useId, type InputHTMLAttributes } from 'react'
import { cx } from '../../lib/utils'

export interface SearchInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string
  hideLabel?: boolean
}

export function SearchInput({ label, hideLabel = true, id, className, ...rest }: SearchInputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  return (
    <div className="flex flex-col gap-sm">
      <label htmlFor={inputId} className={cx('text-sm font-medium text-text-primary', hideLabel && 'sr-only')}>
        {label}
      </label>
      <div className="relative">
        <Search className="pointer-events-none absolute left-lg top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" aria-hidden="true" />
        <input
          id={inputId}
          type="search"
          className={cx(
            'min-h-[44px] w-full rounded-md border border-border-strong bg-surface pl-3xl pr-lg text-base text-text-primary placeholder:text-text-muted',
            className,
          )}
          {...rest}
        />
      </div>
    </div>
  )
}
