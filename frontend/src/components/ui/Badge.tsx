import type { ReactNode } from 'react'

type Tone = 'neutral' | 'brand' | 'success' | 'warning' | 'danger' | 'info'

const TONES: Record<Tone, string> = {
  neutral: 'bg-slate-100 text-slate-700',
  brand: 'bg-brand-50 text-brand-800 ring-1 ring-inset ring-brand-200',
  success: 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200',
  warning: 'bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-200',
  danger: 'bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200',
  info: 'bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-200',
}

export function Badge({ tone = 'neutral', children, className = '' }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${TONES[tone]} ${className}`}>
      {children}
    </span>
  )
}
