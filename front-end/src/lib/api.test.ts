import { describe, expect, it, vi } from 'vitest'

import { ApiClient } from './api'

describe('ApiClient', () => {
  it('attaches gateway headers, bearer token, and guest session id', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: async () => ({ items: [] }),
    })

    const client = new ApiClient({
      baseUrl: 'http://gateway.test',
      clientType: 'web',
      getToken: () => 'Bearer user:user-1',
      getGuestSessionId: () => 'guest-1',
      fetcher: fetchMock,
    })

    await client.request('/api/v1/cart', { method: 'GET' })

    const [, init] = fetchMock.mock.calls[0]
    expect(fetchMock.mock.calls[0][0]).toBe('http://gateway.test/api/v1/cart')
    expect(init.headers.Authorization).toBe('Bearer user:user-1')
    expect(init.headers['X-Client-Type']).toBe('web')
    expect(init.headers['X-Guest-Session-Id']).toBe('guest-1')
    expect(init.headers['X-Request-Id']).toMatch(/^req-/)
  })
})
