import { Loader2 } from 'lucide-react'
import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cx } from '../../lib/utils'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline'
export type ButtonSize = 'sm' | 'md'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  /** Required when `disabled` is true: tells the user why the control is disabled. */
  disabledReason?: string
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-on-primary hover:bg-primary-hover border border-primary',
  secondary: 'bg-surface text-text-primary border border-border-strong hover:bg-muted',
  outline: 'bg-transparent text-primary border border-primary hover:bg-muted',
  ghost: 'bg-transparent text-text-secondary border border-transparent hover:bg-muted',
}

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'min-h-[44px] px-md text-sm gap-sm',
  md: 'min-h-[44px] px-xl text-sm gap-sm',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', loading = false, disabled, disabledReason, className, children, title, ...rest },
  ref,
) {
  const isDisabled = disabled || loading
  return (
    <button
      ref={ref}
      type="button"
      disabled={isDisabled}
      title={disabled && disabledReason ? disabledReason : title}
      aria-disabled={isDisabled}
      className={cx(
        'inline-flex items-center justify-center rounded-md font-sans text-sm font-medium',
        'transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className,
      )}
      {...rest}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  )
})
