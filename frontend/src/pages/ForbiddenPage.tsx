import { ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { HOME_ROUTE_BY_ROLE } from '../lib/nav'

export function ForbiddenPage() {
  const { user } = useAuth()
  const home = user ? HOME_ROUTE_BY_ROLE[user.role] : '/login'

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-md bg-bg px-xl text-center">
      <ShieldAlert className="h-12 w-12 text-critical" aria-hidden="true" />
      <h1 className="text-xl font-semibold text-text-primary">403 - Access denied</h1>
      <p className="max-w-sm text-sm text-text-secondary">
        Your account does not have permission to view this page.
      </p>
      <Link
        to={home}
        className="mt-md inline-flex min-h-[44px] items-center rounded-md bg-primary px-xl text-sm font-medium text-on-primary hover:bg-primary-hover"
      >
        Back to my workspace
      </Link>
    </div>
  )
}
