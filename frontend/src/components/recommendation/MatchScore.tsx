import { scoreTone } from '../../utils/format'

const TONE = {
  excellent: { ring: 'stroke-emerald-500', text: 'text-emerald-700', label: 'Excellent match' },
  good: { ring: 'stroke-brand-600', text: 'text-brand-800', label: 'Good match' },
  fair: { ring: 'stroke-amber-500', text: 'text-amber-700', label: 'Fair match' },
  low: { ring: 'stroke-slate-400', text: 'text-slate-600', label: 'Weak match' },
}

/** Circular match indicator. The number is always shown, so colour is never the only signal. */
export function MatchScore({ score, size = 'md' }: { score: number; size?: 'sm' | 'md' | 'lg' }) {
  const tone = TONE[scoreTone(score)]
  const dimension = { sm: 48, md: 64, lg: 88 }[size]
  const stroke = size === 'lg' ? 7 : 5
  const radius = (dimension - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - Math.min(Math.max(score, 0), 100) / 100)
  return (
    <div className="flex items-center gap-3">
      <div className="relative" style={{ width: dimension, height: dimension }}>
        <svg width={dimension} height={dimension} className="-rotate-90" aria-hidden>
          <circle cx={dimension / 2} cy={dimension / 2} r={radius} fill="none" strokeWidth={stroke} className="stroke-slate-100" />
          <circle
            cx={dimension / 2}
            cy={dimension / 2}
            r={radius}
            fill="none"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={tone.ring}
          />
        </svg>
        <span
          className={`absolute inset-0 flex items-center justify-center font-semibold ${tone.text} ${size === 'lg' ? 'text-2xl' : size === 'md' ? 'text-base' : 'text-sm'}`}
        >
          {Math.round(score)}%
        </span>
      </div>
      {size !== 'sm' && (
        <div>
          <p className={`text-sm font-semibold ${tone.text}`}>{tone.label}</p>
          <p className="text-xs text-slate-500">Match score</p>
        </div>
      )}
    </div>
  )
}
