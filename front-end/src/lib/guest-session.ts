const GUEST_KEY = 'ecommerce.guest_session_id'

export function getGuestSessionId() {
  const existing = sessionStorage.getItem(GUEST_KEY)
  if (existing) return existing
  const next = globalThis.crypto?.randomUUID?.() ?? `guest-${Date.now()}-${Math.random().toString(16).slice(2)}`
  sessionStorage.setItem(GUEST_KEY, next)
  return next
}
