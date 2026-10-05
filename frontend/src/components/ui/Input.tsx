import { forwardRef, useId, type InputHTMLAttributes } from 'react'
import { cx } from '../../lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string | null
  hint?: string
  containerClassName?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, hint, id, className, containerClassName, ...rest },
  ref,
) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const hintId = hint ? `${inputId}-hint` : undefined
  const errorId = error ? `${inputId}-error` : undefined

  return (
    <div className={cx('flex flex-col gap-sm', containerClassName)}>
      <label htmlFor={inputId} className="text-sm font-medium text-text-primary">
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={!!error}
        aria-describedby={cx(hintId, errorId) || undefined}
        className={cx(
          'min-h-[44px] rounded-md border bg-surface px-lg text-base text-text-primary',
          'placeholder:text-text-muted',
          error ? 'border-critical' : 'border-border-strong',
          'disabled:bg-muted disabled:text-text-muted disabled:cursor-not-allowed',
          className,
        )}
        {...rest}
      />
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
