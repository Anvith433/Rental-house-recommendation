import { Link } from 'react-router'
import { Logo } from './Logo'

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 md:grid-cols-4 lg:px-8">
        <div className="md:col-span-2">
          <Logo />
          <p className="mt-3 max-w-sm text-sm text-slate-500">
            Rental homes ranked by what matters to you, with a clear explanation for every recommendation.
          </p>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Explore</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-500">
            <li><Link to="/properties" className="hover:text-slate-800">Browse homes</Link></li>
            <li><Link to="/recommendations" className="hover:text-slate-800">Recommendations</Link></li>
            <li><Link to="/compare" className="hover:text-slate-800">Compare homes</Link></li>
          </ul>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Account</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-500">
            <li><Link to="/dashboard" className="hover:text-slate-800">Dashboard</Link></li>
            <li><Link to="/favorites" className="hover:text-slate-800">Saved homes</Link></li>
            <li><Link to="/profile" className="hover:text-slate-800">Preferences</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-100">
        <p className="mx-auto max-w-7xl px-4 py-5 text-xs text-slate-400 sm:px-6 lg:px-8">
          © {new Date().getFullYear()} RentWise. Demo listings are illustrative.
        </p>
      </div>
    </footer>
  )
}
