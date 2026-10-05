import { Loader2 } from 'lucide-react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import type { Role } from '../types/api'

export function FullPageSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg" role="status" aria-label="Loading">
      <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden="true" />
    </div>
  )
}

export function RoleRoute({ allow }: { allow: Role[] }) {
  const { user, status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageSpinner />

  if (status === 'unauthenticated' || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (!allow.includes(user.role)) {
    return <Navigate to="/403" replace />
  }

  return <Outlet />
}
