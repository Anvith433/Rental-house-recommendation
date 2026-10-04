import { Check, Info, X } from 'lucide-react'
import type { Criterion, Explanation } from '../../types/api'
import { SCORING_WEIGHTS } from '../../utils/constants'
import { CRITERION_LABELS } from '../../utils/format'

// Highest multiplier (must-have) – the most points a criterion can contribute.
const MAX_MULTIPLIER = 1.5

interface ExplanationPanelProps {
  explanation: Explanation
  breakdown?: Partial<Record<Criterion, number>>
  compact?: boolean
}

export function ExplanationPanel({ explanation, breakdown, compact = false }: ExplanationPanelProps) {
  const strengths = compact ? explanation.strengths.slice(0, 4) : explanation.strengths
  return (
    <div className="space-y-3">
      {!compact && <p className="text-sm text-slate-600">{explanation.summary}</p>}
      {strengths.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Why this matches</p>
          <ul className="space-y-1.5">
            {strengths.map((line) => (
              <li key={line} className="flex items-start gap-2 text-sm text-slate-700">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden />
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}
      {explanation.weaknesses.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Potential mismatch</p>
          <ul className="space-y-1.5">
            {explanation.weaknesses.map((line) => (
              <li key={line} className="flex items-start gap-2 text-sm text-slate-700">
                <X className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" aria-hidden />
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}
      {!compact && breakdown && Object.keys(breakdown).length > 0 && (
        <div>
          <p className="mb-2 flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Score breakdown
            <span title="Points per criterion after your priority weighting. Must-have misses cost 20 points; the total is capped at 100.">
              <Info className="h-3.5 w-3.5" aria-hidden />
            </span>
          </p>
          <dl className="space-y-2">
            {(Object.entries(breakdown) as [Criterion, number][]).map(([criterion, points]) => (
              <div key={criterion} className="grid grid-cols-[6rem_1fr_3rem] items-center gap-3 text-sm">
                <dt className="text-slate-600">{CRITERION_LABELS[criterion]}</dt>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-brand-600" style={{ width: `${Math.min(100, (points / (SCORING_WEIGHTS[criterion] * MAX_MULTIPLIER)) * 100)}%` }} />
                </div>
                <dd className="text-right font-medium tabular-nums text-slate-700">{points.toFixed(1)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  )
}
