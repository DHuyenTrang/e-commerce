import { createContext, useContext, useMemo } from 'react'
import type { ReactNode } from 'react'
import { useAuth } from './auth/auth-context'
import { ApiClient, createApi } from './lib/api'
import type { Api } from './lib/api'
import { getGuestSessionId } from './lib/guest-session'

const ApiContext = createContext<Api | null>(null)

export function ApiProvider({ children }: { children: ReactNode }) {
  const auth = useAuth()
  const api = useMemo(() => {
    const client = new ApiClient({
      getToken: () => auth.token,
      getGuestSessionId,
      clientType: auth.isStaff ? 'admin-web' : 'storefront-web',
    })
    return createApi(client)
  }, [auth.isStaff, auth.token])

  return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>
}

export function useApi() {
  const api = useContext(ApiContext)
  if (!api) throw new Error('useApi must be used inside ApiProvider')
  return api
}
