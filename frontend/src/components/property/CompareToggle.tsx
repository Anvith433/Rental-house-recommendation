import { GitCompareArrows } from 'lucide-react'
import { useCompare } from '../../hooks/useCompare'

export function CompareToggle({ propertyId, className = '' }: { propertyId: number; className?: string }) {
  const { has, toggle, isFull } = useCompare()
  const selected = has(propertyId)
  return (
    <button
      type="button"
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
        toggle(propertyId)
      }}
      aria-pressed={selected}
      disabled={!selected && isFull}
      title={!selected && isFull ? 'Comparison is full (4 properties)' : undefined}
      className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
        selected ? 'bg-brand-700 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
      } ${className}`}
    >
      <GitCompareArrows className="h-3.5 w-3.5" aria-hidden />
      {selected ? 'Comparing' : 'Compare'}
    </button>
  )
}
