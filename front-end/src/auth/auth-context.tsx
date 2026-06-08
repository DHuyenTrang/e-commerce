import { createContext, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

const TOKEN_KEY = 'ecommerce.access_token'

export type AuthSubject = {
  type: 'user' | 'staff'
  id: string
  roles: string[]
  permissions: string[]
}

export type AuthContextValue = {
  token: string | null
  subject: AuthSubject | null
  isAuthenticated: boolean
  isStaff: boolean
  loginToken: (token: string) => void
  logout: () => void
  hasPermission: (permission: string) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children, initialToken }: { children: ReactNode; initialToken?: string | null }) {
  const [token, setToken] = useState<string | null>(() => initialToken ?? sessionStorage.getItem(TOKEN_KEY))
  const subject = useMemo(() => parseDevToken(token), [token])

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      subject,
      isAuthenticated: Boolean(token && subject),
      isStaff: subject?.type === 'staff',
      loginToken(nextToken) {
        sessionStorage.setItem(TOKEN_KEY, nextToken)
        setToken(nextToken)
      },
      logout() {
        sessionStorage.removeItem(TOKEN_KEY)
        sessionStorage.removeItem('ecommerce.guest_session_id')
        setToken(null)
      },
      hasPermission(permission) {
        if (!subject) return false
        if (subject.roles.includes('ADMIN')) return true
        return subject.permissions.includes(permission)
      },
    }),
    [subject, token],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}

export function getStoredToken() {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function parseDevToken(token: string | null): AuthSubject | null {
  if (!token) return null
  const raw = token.replace(/^Bearer\s+/i, '')
  const [principal, ...metadataParts] = raw.split(';')
  const [type, id] = principal.split(':')
  if ((type !== 'user' && type !== 'staff') || !id) return null

  const metadata = new Map<string, string>()
  for (const part of metadataParts) {
    const [key, value] = part.split('=')
    if (key && value !== undefined) metadata.set(key, value)
  }

  return {
    type,
    id,
    roles: splitList(metadata.get('roles')),
    permissions: splitList(metadata.get('permissions')),
  }
}

function splitList(value: string | undefined) {
  if (!value) return []
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}
