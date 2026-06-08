import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { ProductListPage } from './product-list-page'

describe('ProductListPage', () => {
  it('renders loading, then empty catalog state', async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const api = {
      products: {
        list: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 }),
      },
    }

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/products']}>
          <ProductListPage api={api} />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    expect(screen.getByText(/loading products/i)).toBeInTheDocument()
    expect(await screen.findByText(/no products found/i)).toBeInTheDocument()
  })
})
