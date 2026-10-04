import { GitCompareArrows, X } from 'lucide-react'
import { useLocation } from 'react-router'
import { useCompare } from '../../hooks/useCompare'
import { MAX_COMPARE } from '../../utils/constants'
import { ButtonLink } from '../ui/Button'

/** Floating shortlist bar shown while the user has properties selected for comparison. */
export function CompareTray() {
  const { ids, clear } = useCompare()
  const { pathname } = useLocation()
  if (ids.length === 0 || pathname === '/compare' || pathname.startsWith('/admin')) return null
  return (
    <div className="fixed inset-x-0 bottom-4 z-30 flex justify-center px-4">
      <div className="flex w-full max-w-md items-center gap-3 rounded-2xl border border-slate-200 bg-white/95 px-4 py-3 shadow-xl backdrop-blur">
        <GitCompareArrows className="h-5 w-5 text-brand-700" aria-hidden />
        <p className="flex-1 text-sm text-slate-700">
          <span className="font-semibold">{ids.length}</span> of {MAX_COMPARE} selected
          {ids.length < 2 && <span className="text-slate-500"> · pick one more</span>}
        </p>
        <button type="button" onClick={clear} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100" aria-label="Clear comparison">
          <X className="h-4 w-4" />
        </button>
        <ButtonLink to="/compare" size="sm" aria-disabled={ids.length < 2} className={ids.length < 2 ? 'pointer-events-none opacity-50' : ''}>
          Compare
        </ButtonLink>
      </div>
    </div>
  )
}
