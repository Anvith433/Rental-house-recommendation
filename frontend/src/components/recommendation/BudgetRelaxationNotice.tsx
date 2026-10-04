import { AlertTriangle } from 'lucide-react'
import type { RecommendationResponse } from '../../types/api'
import { formatRupees } from '../../utils/format'

export function BudgetRelaxationNotice({ response }: { response: RecommendationResponse }) {
  if (!response.budget_relaxed || response.original_max_rent === undefined) return null
  return (
    <div className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900" role="status">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden />
      <div>
        <p className="font-semibold">We couldn't find an exact match within your budget.</p>
        <p className="mt-0.5">
          We increased your budget by {response.relaxation_percentage}% — from{' '}
          <strong>{formatRupees(response.original_max_rent)}</strong> to{' '}
          <strong>{formatRupees(response.relaxed_max_rent)}</strong> — to show the closest options. All your other requirements were kept.
        </p>
      </div>
    </div>
  )
}
