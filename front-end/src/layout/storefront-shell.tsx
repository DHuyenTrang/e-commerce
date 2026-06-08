import { Link, NavLink, Outlet } from 'react-router-dom'
import { Bot, PackageSearch, ShoppingBag, ShoppingCart, UserRound } from 'lucide-react'
import { useAuth } from '../auth/auth-context'
import { Button } from '../ui/button'

export function StorefrontShell() {
  const auth = useAuth()
  return (
    <div className="app-shell">
      <header className="topbar storefront-topbar">
        <Link className="brand" to="/">
          <ShoppingBag size={24} aria-hidden="true" />
          <span>Commerce Hub</span>
        </Link>
        <nav className="nav-links" aria-label="Storefront">
          <NavLink to="/products">
            <PackageSearch size={17} aria-hidden="true" />
            Products
          </NavLink>
          <NavLink to="/cart">
            <ShoppingCart size={17} aria-hidden="true" />
            Cart
          </NavLink>
          <NavLink to="/orders">Orders</NavLink>
          <NavLink to="/assistant">
            <Bot size={17} aria-hidden="true" />
            Assistant
          </NavLink>
        </nav>
        <div className="topbar-actions">
          <NavLink to="/profile" className="icon-link" aria-label="Profile">
            <UserRound size={20} aria-hidden="true" />
          </NavLink>
          {auth.isAuthenticated ? (
            <Button variant="ghost" onClick={auth.logout}>
              Logout
            </Button>
          ) : (
            <Link className="btn btn-secondary" to="/login">
              Login
            </Link>
          )}
        </div>
      </header>
      <main className="page-frame">
        <Outlet />
      </main>
    </div>
  )
}
