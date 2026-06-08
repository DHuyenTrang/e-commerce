import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '../auth/auth-context'
import { AdminShell } from './admin-shell'

describe('AdminShell', () => {
  it('hides admin menu items without matching permissions', () => {
    render(
      <AuthProvider initialToken="Bearer staff:staff-1;roles=STAFF;permissions=comment:moderate">
        <MemoryRouter>
          <AdminShell>
            <div>Admin content</div>
          </AdminShell>
        </MemoryRouter>
      </AuthProvider>,
    )

    expect(screen.queryByRole('link', { name: /products/i })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: /comments/i })).toBeInTheDocument()
  })
})
