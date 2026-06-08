export type Paginated<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type ApiEnvelope<T> = T | { data: T }

export type UserProfile = {
  id: string
  email: string
  full_name?: string
  phone?: string
  addresses?: Address[]
}

export type Address = {
  id?: string
  recipient_name: string
  phone: string
  line1: string
  city: string
  district?: string
  ward?: string
  postal_code?: string
}

export type Product = {
  id: string
  slug: string
  name: string
  description?: string
  price: number
  currency?: string
  image_url?: string
  images?: string[]
  category?: string
  brand?: string
  tags?: string[]
  stock?: number
  rating?: number
  review_count?: number
  status?: string
}

export type CartItem = {
  id: string
  product_id: string
  product?: Product
  name?: string
  quantity: number
  unit_price: number
}

export type Cart = {
  id: string
  items: CartItem[]
  subtotal: number
  currency?: string
}

export type Order = {
  id: string
  status: string
  total: number
  currency?: string
  created_at?: string
  items?: CartItem[]
}

export type PaymentMethod = {
  id: string
  type: string
  label: string
}

export type Shipment = {
  id: string
  carrier: string
  tracking_number?: string
  status: string
  fee?: number
}

export type Review = {
  id: string
  product_id: string
  user_name?: string
  rating: number
  content: string
  visible?: boolean
  reply?: string
}

export type StaffAccount = {
  id: string
  email: string
  full_name?: string
  department?: string
  status?: string
  roles?: string[]
}

export type Role = {
  id: string
  name: string
  permissions: string[]
}
