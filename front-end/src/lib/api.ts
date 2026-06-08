import type {
  ApiEnvelope,
  Cart,
  Order,
  Paginated,
  PaymentMethod,
  Product,
  Review,
  Role,
  Shipment,
  StaffAccount,
  UserProfile,
} from './types'

type RequestBody = BodyInit | Record<string, unknown> | unknown[] | null
type ApiRequestInit = Omit<RequestInit, 'body'> & { body?: RequestBody }

export type ApiClientOptions = {
  baseUrl?: string
  clientType?: string
  getToken?: () => string | null
  getGuestSessionId?: () => string | null
  fetcher?: typeof fetch
  timeoutMs?: number
}

export class ApiError extends Error {
  status: number
  code?: string

  constructor(status: number, message: string, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export class ApiClient {
  private readonly baseUrl: string
  private readonly clientType: string
  private readonly getToken: () => string | null
  private readonly getGuestSessionId: () => string | null
  private readonly fetcher: typeof fetch
  private readonly timeoutMs: number

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl ?? import.meta.env.VITE_API_BASE_URL ?? '')
    this.clientType = options.clientType ?? 'web'
    this.getToken = options.getToken ?? (() => null)
    this.getGuestSessionId = options.getGuestSessionId ?? (() => null)
    this.fetcher = options.fetcher ?? globalThis.fetch.bind(globalThis)
    this.timeoutMs = options.timeoutMs ?? 4_000
  }

  async request<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
    const headers = headersToRecord(init.headers)
    headers['X-Request-Id'] = createRequestId()
    headers['X-Client-Type'] = this.clientType

    const token = this.getToken()
    if (token) headers.Authorization = token

    const guestSessionId = this.getGuestSessionId()
    if (guestSessionId) headers['X-Guest-Session-Id'] = guestSessionId

    const body = init.body
    const isStructuredBody =
      body !== undefined &&
      body !== null &&
      typeof body === 'object' &&
      !(body instanceof FormData) &&
      !(body instanceof URLSearchParams) &&
      !(body instanceof Blob) &&
      !(body instanceof ArrayBuffer)

    if (isStructuredBody && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }

    const controller = init.signal ? null : new AbortController()
    const timeoutId = controller
      ? globalThis.setTimeout(() => controller.abort(new Error('Gateway request timed out')), this.timeoutMs)
      : null

    const response = await this.fetcher(this.url(path), {
      ...init,
      headers,
      body: isStructuredBody ? JSON.stringify(body) : (body as BodyInit | null | undefined),
      signal: init.signal ?? controller?.signal,
    })

    if (timeoutId) globalThis.clearTimeout(timeoutId)

    if (response.status === 204) return undefined as T

    const parsed = await readPayload(response)

    if (!response.ok) {
      const message = extractErrorMessage(parsed) ?? response.statusText ?? 'Request failed'
      throw new ApiError(response.status, message, extractErrorCode(parsed))
    }

    return unwrapEnvelope(parsed) as T
  }

  private url(path: string) {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`
    return `${this.baseUrl}${normalizedPath}`
  }
}

export function createApi(client: ApiClient) {
  return {
    auth: {
      me: () => client.request<UserProfile>('/api/v1/users/me'),
      login: (payload: Record<string, unknown>) =>
        client.request<{ access_token: string; profile?: UserProfile }>('/api/v1/auth/login', {
          method: 'POST',
          body: payload,
        }),
    },
    users: {
      me: () => client.request<UserProfile>('/api/v1/users/me'),
      updateProfile: (payload: Partial<UserProfile>) =>
        client.request<UserProfile>('/api/v1/users/me', { method: 'PATCH', body: payload }),
    },
    products: {
      list: (params: URLSearchParams | Record<string, string | number | undefined> = {}) =>
        client.request<Paginated<Product>>(`/api/v1/products${queryString(params)}`),
      detail: (slug: string) => client.request<Product>(`/api/v1/products/${slug}`),
      create: (payload: Partial<Product>) =>
        client.request<Product>('/api/v1/products', { method: 'POST', body: payload }),
      update: (id: string, payload: Partial<Product>) =>
        client.request<Product>(`/api/v1/products/${id}`, { method: 'PATCH', body: payload }),
      updateStock: (id: string, stock: number) =>
        client.request<Product>(`/api/v1/products/${id}/stock`, { method: 'PATCH', body: { stock } }),
    },
    cart: {
      get: () => client.request<Cart>('/api/v1/cart'),
      add: (productId: string, quantity: number) =>
        client.request<Cart>('/api/v1/cart/items', { method: 'POST', body: { product_id: productId, quantity } }),
      update: (itemId: string, quantity: number) =>
        client.request<Cart>(`/api/v1/cart/items/${itemId}`, { method: 'PATCH', body: { quantity } }),
      remove: (itemId: string) => client.request<Cart>(`/api/v1/cart/items/${itemId}`, { method: 'DELETE' }),
    },
    orders: {
      list: () => client.request<Paginated<Order>>('/api/v1/orders'),
      detail: (id: string) => client.request<Order>(`/api/v1/orders/${id}`),
      place: (payload: Record<string, unknown>) =>
        client.request<Order>('/api/v1/orders', { method: 'POST', body: payload }),
    },
    payments: {
      methods: () => client.request<PaymentMethod[]>('/api/v1/payments/methods'),
      initiate: (orderId: string, methodId: string) =>
        client.request<{ redirect_url?: string; status: string }>('/api/v1/payments', {
          method: 'POST',
          body: { order_id: orderId, payment_method_id: methodId },
        }),
    },
    shipping: {
      rates: (payload: Record<string, unknown>) =>
        client.request<{ fee: number; carrier?: string }>('/api/v1/shipping/rates', {
          method: 'POST',
          body: payload,
        }),
      shipments: () => client.request<Paginated<Shipment>>('/api/v1/shipping/shipments'),
      track: (id: string) => client.request<Shipment>(`/api/v1/shipping/shipments/${id}`),
    },
    comments: {
      list: (productId?: string) =>
        client.request<Paginated<Review>>(`/api/v1/comments${queryString({ product_id: productId })}`),
      create: (payload: Pick<Review, 'product_id' | 'rating' | 'content'>) =>
        client.request<Review>('/api/v1/comments', { method: 'POST', body: payload }),
      moderate: (id: string, payload: Partial<Review>) =>
        client.request<Review>(`/api/v1/comments/${id}`, { method: 'PATCH', body: payload }),
    },
    staff: {
      list: () => client.request<Paginated<StaffAccount>>('/api/v1/staff'),
      create: (payload: Partial<StaffAccount>) =>
        client.request<StaffAccount>('/api/v1/staff', { method: 'POST', body: payload }),
      roles: () => client.request<Paginated<Role>>('/api/v1/staff/roles'),
      assignRole: (staffId: string, roleId: string) =>
        client.request<StaffAccount>(`/api/v1/staff/${staffId}/roles`, {
          method: 'POST',
          body: { role_id: roleId },
        }),
    },
    ai: {
      chat: (message: string) =>
        client.request<{ reply: string }>('/api/v1/ai/chat', { method: 'POST', body: { message } }),
    },
  }
}

export type Api = ReturnType<typeof createApi>

function normalizeBaseUrl(url: string) {
  return url.replace(/\/+$/, '')
}

function createRequestId() {
  if (globalThis.crypto?.randomUUID) return `req-${globalThis.crypto.randomUUID()}`
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function headersToRecord(headers: HeadersInit | undefined) {
  const record: Record<string, string> = {}
  if (!headers) return record
  new Headers(headers).forEach((value, key) => {
    record[key] = value
  })
  return record
}

async function readPayload(response: Response) {
  if ('text' in response && typeof response.text === 'function') {
    const text = await response.text()
    return text ? safeJson(text) : undefined
  }
  if ('json' in response && typeof response.json === 'function') {
    return response.json() as Promise<unknown>
  }
  return undefined
}

function queryString(params: URLSearchParams | Record<string, string | number | undefined>) {
  const search = params instanceof URLSearchParams ? params : new URLSearchParams()
  if (!(params instanceof URLSearchParams)) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') search.set(key, String(value))
    }
  }
  const value = search.toString()
  return value ? `?${value}` : ''
}

function safeJson(text: string) {
  try {
    return JSON.parse(text) as unknown
  } catch {
    return text
  }
}

function unwrapEnvelope<T>(payload: ApiEnvelope<T> | unknown): T | unknown {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as { data: unknown }).data
  }
  return payload
}

function extractErrorMessage(payload: unknown) {
  if (payload && typeof payload === 'object' && 'message' in payload) {
    return String((payload as { message: unknown }).message)
  }
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    return String((payload as { detail: unknown }).detail)
  }
  return undefined
}

function extractErrorCode(payload: unknown) {
  if (payload && typeof payload === 'object' && 'code' in payload) {
    return String((payload as { code: unknown }).code)
  }
  return undefined
}
