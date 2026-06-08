import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Search, ShoppingCart, SlidersHorizontal } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import type { Api } from '../../lib/api'
import type { Product } from '../../lib/types'
import { money } from '../../lib/format'
import { Button } from '../../ui/button'
import { EmptyState, ErrorState, LoadingState } from '../../ui/state'
import { useApi } from '../../app-context'

type ProductListApi = {
  products: Pick<Api['products'], 'list'>
}

export function ProductListPage({ api: providedApi }: { api?: ProductListApi }) {
  const contextApi = useOptionalApi()
  const api = providedApi ?? contextApi
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = useMemo(() => new URLSearchParams(searchParams), [searchParams])
  const query = useQuery({
    queryKey: ['products', filters.toString()],
    queryFn: () => api.products.list(filters),
  })

  function updateFilter(key: string, value: string) {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    next.set('page', '1')
    setSearchParams(next)
  }

  return (
    <section className="content-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Catalog</p>
          <h1>Products</h1>
        </div>
        <div className="filter-row" role="search">
          <Search size={18} aria-hidden="true" />
          <input
            aria-label="Search products"
            placeholder="Search"
            value={searchParams.get('q') ?? ''}
            onChange={(event) => updateFilter('q', event.target.value)}
          />
          <select
            aria-label="Category"
            value={searchParams.get('category') ?? ''}
            onChange={(event) => updateFilter('category', event.target.value)}
          >
            <option value="">All categories</option>
            <option value="electronics">Electronics</option>
            <option value="fashion">Fashion</option>
            <option value="home">Home</option>
          </select>
          <SlidersHorizontal size={18} aria-hidden="true" />
        </div>
      </div>

      {query.isLoading ? <LoadingState label="Loading products" /> : null}
      {query.isError ? <ErrorState detail={(query.error as Error).message} /> : null}
      {query.data && query.data.items.length === 0 ? (
        <EmptyState title="No products found" detail="Adjust filters or create products from the admin portal." />
      ) : null}
      {query.data && query.data.items.length > 0 ? <ProductGrid products={query.data.items} /> : null}
    </section>
  )
}

function ProductGrid({ products }: { products: Product[] }) {
  return (
    <div className="product-grid">
      {products.map((product) => (
        <article className="product-card" key={product.id}>
          <Link to={`/products/${product.slug}`} className="product-media" aria-label={product.name}>
            {product.image_url ? <img src={product.image_url} alt={product.name} /> : <div className="image-placeholder" />}
          </Link>
          <div className="product-body">
            <p className="muted">{product.brand ?? product.category ?? 'Catalog item'}</p>
            <h2>
              <Link to={`/products/${product.slug}`}>{product.name}</Link>
            </h2>
            <div className="product-meta">
              <strong>{money(product.price, product.currency)}</strong>
              <span>{product.stock ?? 0} in stock</span>
            </div>
            <Button className="full-width" variant="secondary">
              <ShoppingCart size={16} aria-hidden="true" />
              Add
            </Button>
          </div>
        </article>
      ))}
    </div>
  )
}

function useOptionalApi() {
  try {
    return useApi()
  } catch {
    return {
      products: {
        list: async () => ({ items: [], total: 0, page: 1, page_size: 20 }),
      },
    } satisfies ProductListApi
  }
}
