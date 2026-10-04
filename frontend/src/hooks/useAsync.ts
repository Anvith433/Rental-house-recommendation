import { useCallback, useEffect, useRef, useState } from 'react'
import { toAppError, type AppError } from '../utils/errors'

export type AsyncDeps = ReadonlyArray<string | number | boolean | null | undefined>

export interface AsyncState<T> {
  data: T | null
  error: AppError | null
  loading: boolean
  reload: () => void
  setData: (updater: (current: T | null) => T | null) => void
}

/**
 * Run an async loader whenever the (primitive) ``deps`` change, tracking
 * loading/error state. Responses from superseded requests are ignored.
 */
export function useAsync<T>(loader: () => Promise<T>, deps: AsyncDeps): AsyncState<T> {
  const [data, setDataState] = useState<T | null>(null)
  const [error, setError] = useState<AppError | null>(null)
  const [loading, setLoading] = useState(true)
  const [reloadCount, setReloadCount] = useState(0)
  const requestKey = `${JSON.stringify(deps)}#${reloadCount}`
  const [settledKey, setSettledKey] = useState(requestKey)
  const loaderRef = useRef(loader)

  useEffect(() => {
    loaderRef.current = loader
  })

  // A new request starts: flip to loading during render rather than in an effect.
  if (settledKey !== requestKey) {
    setSettledKey(requestKey)
    setLoading(true)
    setError(null)
  }

  useEffect(() => {
    let active = true
    loaderRef
      .current()
      .then((result) => {
        if (active) setDataState(result)
      })
      .catch((caught: unknown) => {
        if (active) setError(toAppError(caught))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [requestKey])

  const reload = useCallback(() => setReloadCount((count) => count + 1), [])
  const setData = useCallback((updater: (current: T | null) => T | null) => setDataState(updater), [])

  return { data, error, loading, reload, setData }
}
