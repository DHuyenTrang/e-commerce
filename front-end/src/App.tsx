import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './auth/protected-route'
import { StorefrontShell } from './layout/storefront-shell'
import { AdminShell } from './layout/admin-shell'
import { ProductListPage } from './features/products/product-list-page'
import { HomePage } from './pages/home'
import { LoginPage } from './pages/login'
import {
  AssistantPage,
  CartPage,
  CheckoutPage,
  OrderDetailPage,
  OrdersPage,
  ProductDetailPage,
  ProfilePage,
} from './pages/customer'
import {
  AdminCommentsPage,
  AdminDashboardPage,
  AdminOrdersPage,
  AdminProductNewPage,
  AdminProductsPage,
  AdminRolesPage,
  AdminShippingPage,
  AdminStaffPage,
} from './pages/admin'

export function App() {
  return (
    <Routes>
      <Route element={<StorefrontShell />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="products" element={<ProductListPage />} />
        <Route path="products/:slug" element={<ProductDetailPage />} />
        <Route path="cart" element={<CartPage />} />
        <Route
          path="checkout"
          element={
            <ProtectedRoute>
              <CheckoutPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="orders"
          element={
            <ProtectedRoute>
              <OrdersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="orders/:id"
          element={
            <ProtectedRoute>
              <OrderDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route path="assistant" element={<AssistantPage />} />
      </Route>
      <Route
        path="admin"
        element={
          <ProtectedRoute requireStaff>
            <AdminShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboardPage />} />
        <Route path="products" element={<AdminProductsPage />} />
        <Route path="products/new" element={<AdminProductNewPage />} />
        <Route path="orders" element={<AdminOrdersPage />} />
        <Route path="staff" element={<AdminStaffPage />} />
        <Route path="roles" element={<AdminRolesPage />} />
        <Route path="shipping" element={<AdminShippingPage />} />
        <Route path="comments" element={<AdminCommentsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
