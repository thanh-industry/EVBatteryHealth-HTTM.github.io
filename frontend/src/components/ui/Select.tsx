import { forwardRef, useId, type SelectHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'
import { cx } from '../../lib/utils'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string
  options: SelectOption[]
  error?: string | null
  hint?: string
  containerClassName?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, options, error, hint, id, className, containerClassName, ...rest },
  ref,
) {
  const generatedId = useId()
  const selectId = id ?? generatedId
  const hintId = hint ? `${selectId}-hint` : undefined
  const errorId = error ? `${selectId}-error` : undefined

  return (
    <div className={cx('flex flex-col gap-sm', containerClassName)}>
      <label htmlFor={selectId} className="text-sm font-medium text-text-primary">
        {label}
      </label>
      <div className="relative">
        <select
          ref={ref}
          id={selectId}
          aria-invalid={!!error}
          aria-describedby={cx(hintId, errorId) || undefined}
          className={cx(
            'min-h-[44px] w-full appearance-none rounded-md border bg-surface px-lg pr-3xl text-base text-text-primary',
            error ? 'border-critical' : 'border-border-strong',
            'disabled:bg-muted disabled:text-text-muted disabled:cursor-not-allowed',
            className,
          )}
          {...rest}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} disabled={opt.disabled}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-lg top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted"
          aria-hidden="true"
        />
      </div>
      {hint && !error && (
        <span id={hintId} className="text-caption text-text-muted">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} role="alert" className="text-caption text-critical">
          {error}
        </span>
      )}
    </div>
  )
})
