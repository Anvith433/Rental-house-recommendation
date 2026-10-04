import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useToast } from '../hooks/useToast'
import { MAX_COMPARE } from '../utils/constants'
import { CompareContext } from './contexts'

const STORAGE_KEY = 'rentwise.compare'

function loadIds(): number[] {
  try {
    const parsed: unknown = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(parsed) ? parsed.filter((v): v is number => Number.isInteger(v)).slice(0, MAX_COMPARE) : []
  } catch {
    return []
  }
}

/** The comparison shortlist (property IDs only – nothing sensitive) for this tab. */
export function CompareProvider({ children }: { children: ReactNode }) {
  const [ids, setIds] = useState<number[]>(loadIds)
  const { notify } = useToast()

  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ids))
    } catch {
      // Storage unavailable (private mode); comparison still works in memory.
    }
  }, [ids])

  const toggle = useCallback(
    (id: number) => {
      setIds((current) => {
        if (current.includes(id)) return current.filter((value) => value !== id)
        if (current.length >= MAX_COMPARE) {
          notify(`You can compare up to ${MAX_COMPARE} properties.`, 'info')
          return current
        }
        return [...current, id]
      })
    },
    [notify],
  )

  const remove = useCallback((id: number) => setIds((current) => current.filter((v) => v !== id)), [])
  const clear = useCallback(() => setIds([]), [])

  const value = useMemo(
    () => ({ ids, toggle, remove, clear, has: (id: number) => ids.includes(id), isFull: ids.length >= MAX_COMPARE }),
    [ids, toggle, remove, clear],
  )
  return <CompareContext.Provider value={value}>{children}</CompareContext.Provider>
}
