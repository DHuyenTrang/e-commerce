import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from './auth-context'

export function ProtectedRoute({
  children,
  requireStaff = false,
  permission,
}: {
  children: ReactNode
  requireStaff?: boolean
  permission?: string
}) {
  const auth = useAuth()

  if (!auth.isAuthenticated) return <Navigate to="/login" replace />
  if (requireStaff && !auth.isStaff) return <Navigate to="/login" replace />
  if (permission && !auth.hasPermission(permission)) return <Forbidden />

  return <>{children}</>
}

function Forbidden() {
  return (
    <main className="center-panel">
      <h1>Access denied</h1>
      <p>Your staff token does not include the permission required for this workspace.</p>
    </main>
  )
}
