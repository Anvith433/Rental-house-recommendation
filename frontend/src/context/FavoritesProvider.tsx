import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router'
import { useAuth } from '../hooks/useAuth'
import { useToast } from '../hooks/useToast'
import { favoriteService } from '../services/favoriteService'
import { toAppError } from '../utils/errors'
import { FavoritesContext } from './contexts'

const EMPTY: Set<number> = new Set()

/** Keeps the signed-in user's favorite IDs in memory so every card can show heart state. */
export function FavoritesProvider({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const { notify } = useToast()
  const navigate = useNavigate()
  const [loadedIds, setIds] = useState<Set<number>>(EMPTY)
  const [pending, setPending] = useState<Set<number>>(EMPTY)
  const ids = status === 'authenticated' ? loadedIds : EMPTY

  useEffect(() => {
    if (status !== 'authenticated') return
    let cancelled = false
    favoriteService
      .ids()
      .then((loaded) => !cancelled && setIds(new Set(loaded)))
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [status])

  const toggle = useCallback(
    async (id: number) => {
      if (status !== 'authenticated') {
        notify('Sign in to save properties.', 'info')
        navigate('/login', { state: { from: window.location.pathname } })
        return
      }
      const wasFavorite = ids.has(id)
      const optimistic = new Set(ids)
      if (wasFavorite) optimistic.delete(id)
      else optimistic.add(id)
      setIds(optimistic)
      setPending((current) => new Set(current).add(id))
      try {
        if (wasFavorite) await favoriteService.remove(id)
        else await favoriteService.add(id)
        notify(wasFavorite ? 'Removed from saved properties.' : 'Saved to your favorites.', 'success')
      } catch (error) {
        setIds(ids)
        notify(toAppError(error).message, 'error')
      } finally {
        setPending((current) => {
          const next = new Set(current)
          next.delete(id)
          return next
        })
      }
    },
    [ids, status, notify, navigate],
  )

  const value = useMemo(
    () => ({ ids, pending, toggle, isFavorite: (id: number) => ids.has(id) }),
    [ids, pending, toggle],
  )
  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>
}
