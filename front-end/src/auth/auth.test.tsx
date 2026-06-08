import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from './auth-context'
import { ProtectedRoute } from './protected-route'

describe('ProtectedRoute', () => {
  it('redirects unauthenticated users to login', () => {
    render(
      <AuthProvider initialToken={null}>
        <MemoryRouter initialEntries={['/cart']}>
          <Routes>
            <Route path="/login" element={<div>Login screen</div>} />
            <Route
              path="/cart"
              element={
                <ProtectedRoute>
                  <div>Cart screen</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    )

    expect(screen.getByText('Login screen')).toBeInTheDocument()
  })

  it('allows staff routes when required permission exists', () => {
    render(
      <AuthProvider initialToken="Bearer staff:staff-1;roles=ADMIN;permissions=product:create,product:update">
        <MemoryRouter initialEntries={['/admin/products/new']}>
          <Routes>
            <Route path="/login" element={<div>Login screen</div>} />
            <Route
              path="/admin/products/new"
              element={
                <ProtectedRoute requireStaff permission="product:create">
                  <div>Create product</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    )

    expect(screen.getByText('Create product')).toBeInTheDocument()
  })
})
