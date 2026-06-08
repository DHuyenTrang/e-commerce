import type { ReactNode } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { Boxes, ClipboardList, LayoutDashboard, MessageSquareText, ShieldCheck, Truck, UsersRound } from 'lucide-react'
import { useAuth } from '../auth/auth-context'

const adminMenu = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/admin/products', label: 'Products', permission: 'product:create', icon: Boxes },
  { to: '/admin/orders', label: 'Orders', permission: 'order:read', icon: ClipboardList },
  { to: '/admin/staff', label: 'Staff', permission: 'staff:read', icon: UsersRound },
  { to: '/admin/roles', label: 'Roles', permission: 'role:read', icon: ShieldCheck },
  { to: '/admin/shipping', label: 'Shipping', permission: 'shipping:manage', icon: Truck },
  { to: '/admin/comments', label: 'Comments', permission: 'comment:moderate', icon: MessageSquareText },
]

export function AdminShell({ children }: { children?: ReactNode }) {
  const auth = useAuth()
  const visibleMenu = adminMenu.filter((item) => !item.permission || auth.hasPermission(item.permission))

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div className="admin-brand">Admin Portal</div>
        <nav aria-label="Admin">
          {visibleMenu.map((item) => {
            const Icon = item.icon
            return (
              <NavLink key={item.to} to={item.to} end={item.to === '/admin'}>
                <Icon size={18} aria-hidden="true" />
                {item.label}
              </NavLink>
            )
          })}
        </nav>
      </aside>
      <main className="admin-main">{children ?? <Outlet />}</main>
    </div>
  )
}
