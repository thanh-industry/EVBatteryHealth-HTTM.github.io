import { Compass } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { HOME_ROUTE_BY_ROLE } from '../lib/nav'

export function NotFoundPage() {
  const { user } = useAuth()
  const home = user ? HOME_ROUTE_BY_ROLE[user.role] : '/login'

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-md bg-bg px-xl text-center">
      <Compass className="h-12 w-12 text-text-muted" aria-hidden="true" />
      <h1 className="text-xl font-semibold text-text-primary">404 - Page not found</h1>
      <p className="max-w-sm text-sm text-text-secondary">The page you are looking for does not exist.</p>
      <Link
        to={home}
        className="mt-md inline-flex min-h-[44px] items-center rounded-md bg-primary px-xl text-sm font-medium text-on-primary hover:bg-primary-hover"
      >
        Back to my workspace
      </Link>
    </div>
  )
}
