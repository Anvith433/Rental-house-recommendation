import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { onSessionExpired } from '../services/api'
import { authService, type RegisterPayload } from '../services/authService'
import type { User } from '../types/api'
import { AuthContext, type AuthStatus } from './contexts'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  useEffect(() => {
    let cancelled = false
    authService
      .restoreSession()
      .catch(() => null)
      .then((restored) => {
        if (cancelled) return
        setUserState(restored)
        setStatus(restored ? 'authenticated' : 'anonymous')
      })
    onSessionExpired(() => {
      setUserState(null)
      setStatus('anonymous')
    })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const signedIn = await authService.login(email, password)
    setUserState(signedIn)
    setStatus('authenticated')
    return signedIn
  }, [])

  const register = useCallback(async (payload: RegisterPayload) => {
    const created = await authService.register(payload)
    setUserState(created)
    setStatus('authenticated')
    return created
  }, [])

  const logout = useCallback(async () => {
    try {
      await authService.logout()
    } finally {
      setUserState(null)
      setStatus('anonymous')
    }
  }, [])

  const setUser = useCallback((next: User) => setUserState(next), [])

  const value = useMemo(
    () => ({ user, status, login, register, logout, setUser }),
    [user, status, login, register, logout, setUser],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
