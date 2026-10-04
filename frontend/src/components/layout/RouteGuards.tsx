import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { useAuth } from '../../hooks/useAuth'
import { Spinner } from '../ui/Feedback'

/**
 * Client-side guards improve UX only; every protected endpoint is enforced
 * by the API's permission classes regardless of what the UI shows.
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <Spinner label="Checking your session" />
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <>{children}</>
}

export function AdminRoute({ children }: { children: ReactNode }) {
  const { status, user } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <Spinner label="Checking your session" />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (!user.is_admin) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export function GuestRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  if (status === 'loading') return <Spinner />
  if (status === 'authenticated') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
