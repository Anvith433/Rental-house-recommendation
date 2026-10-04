import { Link } from 'react-router'

export function Logo({ className = '' }: { className?: string }) {
  return (
    <Link to="/" className={`flex items-center gap-2 font-semibold text-slate-900 ${className}`} aria-label="RentWise home">
      <svg viewBox="0 0 64 64" className="h-8 w-8" aria-hidden>
        <rect width="64" height="64" rx="14" fill="#0f766e" />
        <path d="M14 32 32 16l18 16v16a2 2 0 0 1-2 2H38V38H26v12H16a2 2 0 0 1-2-2z" fill="#fff" />
        <circle cx="46" cy="18" r="6" fill="#fbbf24" />
      </svg>
      <span className="text-lg tracking-tight">
        Rent<span className="text-brand-700">Wise</span>
      </span>
    </Link>
  )
}
