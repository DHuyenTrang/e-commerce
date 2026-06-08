import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Bot, CreditCard, Minus, Plus, Send, Trash2 } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useApi } from '../app-context'
import { Button } from '../ui/button'
import { EmptyState, ErrorState, LoadingState } from '../ui/state'
import { money, statusLabel } from '../lib/format'

export function ProductDetailPage() {
  const api = useApi()
  const params = useParams()
  const slug = params.slug ?? ''
  const product = useQuery({ queryKey: ['product', slug], queryFn: () => api.products.detail(slug), enabled: Boolean(slug) })
  const queryClient = useQueryClient()
  const addToCart = useMutation({
    mutationFn: () => api.cart.add(product.data?.id ?? '', 1),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['cart'] }),
  })

  if (product.isLoading) return <LoadingState label="Loading product" />
  if (product.isError) return <ErrorState detail={(product.error as Error).message} />
  if (!product.data) return <EmptyState title="Product not found" />

  return (
    <section className="detail-layout">
      <div className="detail-media">
        {product.data.image_url ? <img src={product.data.image_url} alt={product.data.name} /> : <div className="image-placeholder" />}
      </div>
      <div className="detail-copy">
        <p className="eyebrow">{product.data.brand ?? product.data.category ?? 'Product'}</p>
        <h1>{product.data.name}</h1>
        <strong className="price">{money(product.data.price, product.data.currency)}</strong>
        <p>{product.data.description ?? 'Product details are loaded from the Gateway catalog endpoint.'}</p>
        <p className="muted">{product.data.stock ?? 0} available</p>
        <Button onClick={() => addToCart.mutate()} disabled={addToCart.isPending}>
          Add to cart
        </Button>
        {addToCart.isError ? <p className="form-error">{(addToCart.error as Error).message}</p> : null}
      </div>
      <Reviews productId={product.data.id} />
    </section>
  )
}

export function CartPage() {
  const api = useApi()
  const queryClient = useQueryClient()
  const cart = useQuery({ queryKey: ['cart'], queryFn: api.cart.get })
  const update = useMutation({
    mutationFn: ({ id, quantity }: { id: string; quantity: number }) => api.cart.update(id, quantity),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['cart'] }),
  })
  const remove = useMutation({
    mutationFn: (id: string) => api.cart.remove(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['cart'] }),
  })

  if (cart.isLoading) return <LoadingState label="Loading cart" />
  if (cart.isError) return <ErrorState detail={(cart.error as Error).message} />
  if (!cart.data || cart.data.items.length === 0) return <EmptyState title="Your cart is empty" detail="Catalog items will appear here after add-to-cart succeeds." />

  return (
    <section className="content-section narrow">
      <div className="section-heading">
        <h1>Cart</h1>
        <Link className="btn btn-primary" to="/checkout">
          Checkout
        </Link>
      </div>
      <div className="list-panel">
        {cart.data.items.map((item) => (
          <div className="line-item" key={item.id}>
            <div>
              <strong>{item.product?.name ?? item.name ?? item.product_id}</strong>
              <p>{money(item.unit_price, cart.data.currency)}</p>
            </div>
            <div className="quantity-control">
              <Button variant="ghost" aria-label="Decrease quantity" onClick={() => update.mutate({ id: item.id, quantity: Math.max(1, item.quantity - 1) })}>
                <Minus size={16} aria-hidden="true" />
              </Button>
              <span>{item.quantity}</span>
              <Button variant="ghost" aria-label="Increase quantity" onClick={() => update.mutate({ id: item.id, quantity: item.quantity + 1 })}>
                <Plus size={16} aria-hidden="true" />
              </Button>
              <Button variant="danger" aria-label="Remove item" onClick={() => remove.mutate(item.id)}>
                <Trash2 size={16} aria-hidden="true" />
              </Button>
            </div>
          </div>
        ))}
        <div className="total-row">
          <span>Subtotal</span>
          <strong>{money(cart.data.subtotal, cart.data.currency)}</strong>
        </div>
      </div>
    </section>
  )
}

export function CheckoutPage() {
  const api = useApi()
  const [paymentMethod, setPaymentMethod] = useState('')
  const cart = useQuery({ queryKey: ['cart'], queryFn: api.cart.get })
  const profile = useQuery({ queryKey: ['profile'], queryFn: api.users.me, retry: false })
  const payments = useQuery({ queryKey: ['payment-methods'], queryFn: api.payments.methods, retry: false })
  const placeOrder = useMutation({
    mutationFn: () =>
      api.orders.place({
        payment_method_id: paymentMethod,
        address: profile.data?.addresses?.[0],
      }),
  })

  return (
    <section className="content-section narrow">
      <div className="section-heading">
        <h1>Checkout</h1>
      </div>
      {cart.isLoading ? <LoadingState label="Loading checkout" /> : null}
      {cart.isError ? <ErrorState detail={(cart.error as Error).message} /> : null}
      {cart.data ? (
        <div className="checkout-grid">
          <div className="panel">
            <h2>Address</h2>
            {profile.data?.addresses?.[0] ? <p>{profile.data.addresses[0].line1}, {profile.data.addresses[0].city}</p> : <p className="muted">No saved address returned by User service.</p>}
          </div>
          <div className="panel">
            <h2>Payment</h2>
            {payments.data ? (
              <select aria-label="Payment method" value={paymentMethod} onChange={(event) => setPaymentMethod(event.target.value)}>
                <option value="">Select payment</option>
                {payments.data.map((method) => (
                  <option key={method.id} value={method.id}>
                    {method.label}
                  </option>
                ))}
              </select>
            ) : (
              <p className="muted">Payment methods endpoint is not available yet.</p>
            )}
          </div>
          <div className="panel summary-panel">
            <h2>Total</h2>
            <strong>{money(cart.data.subtotal, cart.data.currency)}</strong>
            <Button onClick={() => placeOrder.mutate()} disabled={placeOrder.isPending || cart.data.items.length === 0}>
              <CreditCard size={17} aria-hidden="true" />
              Place order
            </Button>
            {placeOrder.isError ? <p className="form-error">{(placeOrder.error as Error).message}</p> : null}
            {placeOrder.data ? <p className="success-line">Order {placeOrder.data.id} created.</p> : null}
          </div>
        </div>
      ) : null}
    </section>
  )
}

export function OrdersPage() {
  const api = useApi()
  const orders = useQuery({ queryKey: ['orders'], queryFn: api.orders.list, retry: false })

  if (orders.isLoading) return <LoadingState label="Loading orders" />
  if (orders.isError) return <ErrorState detail={(orders.error as Error).message} />
  if (!orders.data || orders.data.items.length === 0) return <EmptyState title="No orders yet" />

  return (
    <section className="content-section narrow">
      <h1>Orders</h1>
      <div className="list-panel">
        {orders.data.items.map((order) => (
          <Link className="line-item" to={`/orders/${order.id}`} key={order.id}>
            <strong>Order {order.id}</strong>
            <span>{statusLabel(order.status)}</span>
            <strong>{money(order.total, order.currency)}</strong>
          </Link>
        ))}
      </div>
    </section>
  )
}

export function OrderDetailPage() {
  const api = useApi()
  const params = useParams()
  const order = useQuery({ queryKey: ['order', params.id], queryFn: () => api.orders.detail(params.id ?? ''), enabled: Boolean(params.id) })

  if (order.isLoading) return <LoadingState label="Loading order" />
  if (order.isError) return <ErrorState detail={(order.error as Error).message} />
  if (!order.data) return <EmptyState title="Order not found" />

  return (
    <section className="content-section narrow">
      <h1>Order {order.data.id}</h1>
      <div className="panel">
        <p>Status: {statusLabel(order.data.status)}</p>
        <strong>{money(order.data.total, order.data.currency)}</strong>
      </div>
    </section>
  )
}

export function ProfilePage() {
  const api = useApi()
  const profile = useQuery({ queryKey: ['profile'], queryFn: api.users.me, retry: false })
  if (profile.isLoading) return <LoadingState label="Loading profile" />
  if (profile.isError) return <ErrorState detail={(profile.error as Error).message} />
  return (
    <section className="content-section narrow">
      <h1>Profile</h1>
      <div className="panel">
        <strong>{profile.data?.full_name ?? profile.data?.email ?? 'Customer'}</strong>
        <p>{profile.data?.phone ?? 'No phone number'}</p>
      </div>
    </section>
  )
}

export function AssistantPage() {
  const api = useApi()
  const [message, setMessage] = useState('')
  const [history, setHistory] = useState<Array<{ role: string; text: string }>>([])
  const chat = useMutation({
    mutationFn: api.ai.chat,
    onSuccess(data, sent) {
      setHistory((current) => [...current, { role: 'You', text: sent }, { role: 'Assistant', text: data.reply }])
      setMessage('')
    },
  })

  return (
    <section className="content-section narrow">
      <div className="section-heading">
        <h1>Assistant</h1>
        <Bot size={24} aria-hidden="true" />
      </div>
      <div className="chat-panel">
        {history.length === 0 ? <EmptyState title="Assistant unavailable until AI service responds" /> : null}
        {history.map((item, index) => (
          <div className="chat-bubble" key={`${item.role}-${index}`}>
            <strong>{item.role}</strong>
            <p>{item.text}</p>
          </div>
        ))}
        {chat.isError ? <ErrorState detail={(chat.error as Error).message} /> : null}
      </div>
      <form className="chat-form" onSubmit={(event) => {
        event.preventDefault()
        if (message.trim()) chat.mutate(message.trim())
      }}>
        <input aria-label="Message" value={message} onChange={(event) => setMessage(event.target.value)} />
        <Button type="submit" disabled={chat.isPending}>
          <Send size={17} aria-hidden="true" />
          Send
        </Button>
      </form>
    </section>
  )
}

function Reviews({ productId }: { productId: string }) {
  const api = useApi()
  const reviews = useQuery({ queryKey: ['reviews', productId], queryFn: () => api.comments.list(productId), retry: false })
  const visible = useMemo(() => reviews.data?.items.filter((review) => review.visible !== false) ?? [], [reviews.data])

  return (
    <section className="reviews-panel">
      <h2>Reviews</h2>
      {reviews.isError ? <p className="muted">Reviews are unavailable.</p> : null}
      {visible.length === 0 && !reviews.isError ? <p className="muted">No visible reviews.</p> : null}
      {visible.map((review) => (
        <article className="panel" key={review.id}>
          <strong>{review.rating}/5</strong>
          <p>{review.content}</p>
          {review.reply ? <p className="muted">Reply: {review.reply}</p> : null}
        </article>
      ))}
    </section>
  )
}
