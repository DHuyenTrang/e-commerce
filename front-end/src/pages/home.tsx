import { Link } from 'react-router-dom'
import { ArrowRight, PackageCheck, ShieldCheck, Truck } from 'lucide-react'
import heroAsset from '../assets/hero.png'

export function HomePage() {
  return (
    <section className="home-layout">
      <div className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Customer storefront</p>
          <h1>Commerce Hub</h1>
          <p>
            Browse inventory, manage cart checkout, review order status, and keep customer support flows ready for the
            API Gateway.
          </p>
          <Link className="btn btn-primary" to="/products">
            Shop products
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </div>
        <div className="hero-side">
          <img className="hero-asset" src={heroAsset} alt="Layered commerce workspace" />
          <div className="hero-inventory" aria-label="Storefront status">
            <div>
              <PackageCheck size={22} aria-hidden="true" />
              <strong>Catalog</strong>
              <span>Search, filters, product detail</span>
            </div>
            <div>
              <Truck size={22} aria-hidden="true" />
              <strong>Fulfillment</strong>
              <span>Shipping rates and tracking views</span>
            </div>
            <div>
              <ShieldCheck size={22} aria-hidden="true" />
              <strong>Gateway-only</strong>
              <span>All calls use /api/v1 routes</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
