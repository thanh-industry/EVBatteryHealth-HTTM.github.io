import { BatteryCharging } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import { HOME_ROUTE_BY_ROLE } from '../lib/nav'

const DEMO_ACCOUNTS = [
  { email: 'scientist@evsoh.io', label: 'Data Scientist' },
  { email: 'tech@evsoh.io', label: 'Technician' },
  { email: 'owner@evsoh.io', label: 'EV Owner' },
]
const DEMO_PASSWORD = 'demo1234'

interface LocationState {
  from?: { pathname: string }
}

export function LoginPage() {
  const { login, user, status } = useAuth()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (status === 'authenticated' && user) {
    const state = location.state as LocationState | null
    const target = state?.from?.pathname ?? HOME_ROUTE_BY_ROLE[user.role]
    return <Navigate to={target} replace />
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login failed. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-xl py-3xl">
      <div className="w-full max-w-md rounded-lg border border-border bg-surface p-2xl shadow-md">
        <div className="mb-xl flex items-center gap-md">
          <BatteryCharging className="h-8 w-8 text-primary" aria-hidden="true" />
          <div>
            <h1 className="text-xl font-semibold text-text-primary">EV Battery SoH Console</h1>
            <p className="text-sm text-text-secondary">Sign in to continue</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-lg" noValidate>
          <Input
            label="Email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && (
            <p role="alert" className="text-sm text-critical">
              {error}
            </p>
          )}
          <Button type="submit" loading={submitting}>
            Sign in
          </Button>
        </form>

        <div className="mt-xl border-t border-border pt-lg">
          <p className="mb-md text-caption font-medium uppercase tracking-wide text-text-muted">
            Demo accounts (password: {DEMO_PASSWORD})
          </p>
          <div className="flex flex-col gap-md">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                type="button"
                onClick={() => {
                  setEmail(acc.email)
                  setPassword(DEMO_PASSWORD)
                }}
                className="flex min-h-[44px] items-center justify-between rounded-md border border-border-strong px-lg text-sm text-text-primary hover:bg-muted"
              >
                <span>{acc.label}</span>
                <span className="font-mono text-caption text-text-muted">{acc.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
