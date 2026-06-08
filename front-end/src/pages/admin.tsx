import { useState } from 'react'
import { Boxes, Plus, Save } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useApi } from '../app-context'
import { Button } from '../ui/button'
import { EmptyState, ErrorState, LoadingState } from '../ui/state'
import { money, statusLabel } from '../lib/format'

export function AdminDashboardPage() {
  const api = useApi()
  const products = useQuery({ queryKey: ['admin-products-summary'], queryFn: () => api.products.list({ page_size: 5 }), retry: false })
  const staff = useQuery({ queryKey: ['admin-staff-summary'], queryFn: api.staff.list, retry: false })
  const comments = useQuery({ queryKey: ['admin-comments-summary'], queryFn: () => api.comments.list(), retry: false })

  return (
    <section className="content-section">
      <h1>Dashboard</h1>
      <div className="metric-grid">
        <Metric label="Products" value={products.data?.total ?? 0} />
        <Metric label="Staff" value={staff.data?.total ?? 0} />
        <Metric label="Comments" value={comments.data?.total ?? 0} />
      </div>
    </section>
  )
}

export function AdminProductsPage() {
  const api = useApi()
  const queryClient = useQueryClient()
  const products = useQuery({ queryKey: ['admin-products'], queryFn: () => api.products.list({ page_size: 50 }), retry: false })
  const stock = useMutation({
    mutationFn: ({ id, value }: { id: string; value: number }) => api.products.updateStock(id, value),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['admin-products'] }),
  })

  if (products.isLoading) return <LoadingState label="Loading products" />
  if (products.isError) return <ErrorState detail={(products.error as Error).message} />
  if (!products.data || products.data.items.length === 0) return <EmptyState title="No products found" />

  return (
    <section className="content-section">
      <div className="section-heading">
        <h1>Product management</h1>
        <a className="btn btn-primary" href="/admin/products/new">
          <Plus size={17} aria-hidden="true" />
          New
        </a>
      </div>
      <div className="table-panel">
        {products.data.items.map((product) => (
          <div className="table-row" key={product.id}>
            <div>
              <strong>{product.name}</strong>
              <p>{product.category ?? 'Uncategorized'} · {money(product.price, product.currency)}</p>
            </div>
            <form
              className="inline-form"
              onSubmit={(event) => {
                event.preventDefault()
                const form = new FormData(event.currentTarget)
                stock.mutate({ id: product.id, value: Number(form.get('stock') ?? product.stock ?? 0) })
              }}
            >
              <input name="stock" aria-label={`${product.name} stock`} type="number" min="0" defaultValue={product.stock ?? 0} />
              <Button type="submit" variant="secondary">
                <Save size={16} aria-hidden="true" />
                Stock
              </Button>
            </form>
          </div>
        ))}
      </div>
    </section>
  )
}

export function AdminProductNewPage() {
  const api = useApi()
  const [form, setForm] = useState({ name: '', slug: '', price: '0', category: '', brand: '', stock: '0' })
  const create = useMutation({
    mutationFn: () =>
      api.products.create({
        name: form.name,
        slug: form.slug,
        price: Number(form.price),
        category: form.category,
        brand: form.brand,
        stock: Number(form.stock),
      }),
  })

  return (
    <section className="content-section narrow">
      <h1>Create product</h1>
      <form className="panel form-grid" onSubmit={(event) => {
        event.preventDefault()
        create.mutate()
      }}>
        {(['name', 'slug', 'price', 'category', 'brand', 'stock'] as const).map((field) => (
          <label key={field}>
            {field}
            <input value={form[field]} onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))} required={field === 'name' || field === 'slug'} />
          </label>
        ))}
        <Button type="submit" disabled={create.isPending}>
          <Boxes size={17} aria-hidden="true" />
          Create
        </Button>
        {create.isError ? <p className="form-error">{(create.error as Error).message}</p> : null}
        {create.data ? <p className="success-line">Created {create.data.name}</p> : null}
      </form>
    </section>
  )
}

export function AdminOrdersPage() {
  const api = useApi()
  const orders = useQuery({ queryKey: ['admin-orders'], queryFn: api.orders.list, retry: false })
  if (orders.isLoading) return <LoadingState label="Loading orders" />
  if (orders.isError) return <ErrorState detail={(orders.error as Error).message} />
  if (!orders.data || orders.data.items.length === 0) return <EmptyState title="No orders yet" />
  return (
    <section className="content-section">
      <h1>Orders</h1>
      <div className="table-panel">
        {orders.data.items.map((order) => (
          <div className="table-row" key={order.id}>
            <strong>{order.id}</strong>
            <span>{statusLabel(order.status)}</span>
            <strong>{money(order.total, order.currency)}</strong>
          </div>
        ))}
      </div>
    </section>
  )
}

export function AdminStaffPage() {
  const api = useApi()
  const staff = useQuery({ queryKey: ['admin-staff'], queryFn: api.staff.list, retry: false })
  if (staff.isLoading) return <LoadingState label="Loading staff" />
  if (staff.isError) return <ErrorState detail={(staff.error as Error).message} />
  return (
    <section className="content-section">
      <h1>Staff</h1>
      {!staff.data || staff.data.items.length === 0 ? <EmptyState title="No staff accounts" /> : null}
      <div className="table-panel">
        {staff.data?.items.map((item) => (
          <div className="table-row" key={item.id}>
            <strong>{item.full_name ?? item.email}</strong>
            <span>{item.department ?? 'General'}</span>
            <span>{statusLabel(item.status)}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export function AdminRolesPage() {
  const api = useApi()
  const roles = useQuery({ queryKey: ['admin-roles'], queryFn: api.staff.roles, retry: false })
  if (roles.isLoading) return <LoadingState label="Loading roles" />
  if (roles.isError) return <ErrorState detail={(roles.error as Error).message} />
  return (
    <section className="content-section">
      <h1>Roles</h1>
      {!roles.data || roles.data.items.length === 0 ? <EmptyState title="No roles found" /> : null}
      <div className="table-panel">
        {roles.data?.items.map((role) => (
          <div className="table-row" key={role.id}>
            <strong>{role.name}</strong>
            <span>{role.permissions.join(', ')}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export function AdminShippingPage() {
  const api = useApi()
  const shipments = useQuery({ queryKey: ['admin-shipments'], queryFn: api.shipping.shipments, retry: false })
  if (shipments.isLoading) return <LoadingState label="Loading shipping" />
  if (shipments.isError) return <ErrorState detail={(shipments.error as Error).message} />
  return (
    <section className="content-section">
      <h1>Shipping</h1>
      {!shipments.data || shipments.data.items.length === 0 ? <EmptyState title="No shipments" /> : null}
      <div className="table-panel">
        {shipments.data?.items.map((shipment) => (
          <div className="table-row" key={shipment.id}>
            <strong>{shipment.carrier}</strong>
            <span>{shipment.tracking_number ?? shipment.id}</span>
            <span>{statusLabel(shipment.status)}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

export function AdminCommentsPage() {
  const api = useApi()
  const queryClient = useQueryClient()
  const comments = useQuery({ queryKey: ['admin-comments'], queryFn: () => api.comments.list(), retry: false })
  const moderate = useMutation({
    mutationFn: ({ id, visible }: { id: string; visible: boolean }) => api.comments.moderate(id, { visible }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['admin-comments'] }),
  })

  if (comments.isLoading) return <LoadingState label="Loading comments" />
  if (comments.isError) return <ErrorState detail={(comments.error as Error).message} />
  if (!comments.data || comments.data.items.length === 0) return <EmptyState title="No comments" />

  return (
    <section className="content-section">
      <h1>Comments</h1>
      <div className="table-panel">
        {comments.data.items.map((comment) => (
          <div className="table-row" key={comment.id}>
            <div>
              <strong>{comment.rating}/5</strong>
              <p>{comment.content}</p>
            </div>
            <Button variant="secondary" onClick={() => moderate.mutate({ id: comment.id, visible: comment.visible === false })}>
              {comment.visible === false ? 'Show' : 'Hide'}
            </Button>
          </div>
        ))}
      </div>
    </section>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
