import { Heart } from 'lucide-react'
import { useFavorites } from '../../hooks/useFavorites'

interface FavoriteButtonProps {
  propertyId: number
  variant?: 'icon' | 'full'
  className?: string
}

export function FavoriteButton({ propertyId, variant = 'icon', className = '' }: FavoriteButtonProps) {
  const { isFavorite, toggle, pending } = useFavorites()
  const saved = isFavorite(propertyId)
  const busy = pending.has(propertyId)
  const label = saved ? 'Remove from saved' : 'Save property'

  if (variant === 'full') {
    return (
      <button
        type="button"
        onClick={() => toggle(propertyId)}
        disabled={busy}
        aria-pressed={saved}
        className={`inline-flex h-10 items-center justify-center gap-2 rounded-lg border px-4 text-sm font-medium transition-colors disabled:opacity-60 ${
          saved
            ? 'border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100'
            : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
        } ${className}`}
      >
        <Heart className={`h-4 w-4 ${saved ? 'fill-rose-500 text-rose-500' : ''}`} aria-hidden />
        {saved ? 'Saved' : 'Save'}
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
        toggle(propertyId)
      }}
      disabled={busy}
      aria-pressed={saved}
      aria-label={label}
      title={label}
      className={`flex h-9 w-9 items-center justify-center rounded-full bg-white/95 shadow-sm ring-1 ring-slate-200 transition hover:scale-105 disabled:opacity-60 ${className}`}
    >
      <Heart className={`h-4 w-4 ${saved ? 'fill-rose-500 text-rose-500' : 'text-slate-600'}`} aria-hidden />
    </button>
  )
}
