import { AlertOctagon, WifiOff } from 'lucide-react'
import { ApiError } from '../../lib/api'
import { Button } from '../ui/Button'

export interface ErrorStateProps {
  error: unknown
  onRetry?: () => void
  title?: string
}

function messageFor(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Something went wrong. Please try again.'
}

export function ErrorState({ error, onRetry, title = 'Could not load this data' }: ErrorStateProps) {
  const isNetwork = error instanceof ApiError && error.status === 0
  const Icon = isNetwork ? WifiOff : AlertOctagon

  return (
    <div className="flex flex-col items-center justify-center gap-md rounded-lg border border-critical bg-critical-bg px-xl py-3xl text-center">
      <Icon className="h-10 w-10 text-critical" aria-hidden="true" />
      <h3 className="text-sm font-semibold text-critical">{title}</h3>
      <p role="alert" className="max-w-sm text-sm text-text-secondary">
        {messageFor(error)}
      </p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  )
}
