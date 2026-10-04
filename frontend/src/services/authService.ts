import { api, refreshAccessToken, setAccessToken } from './api'
import type { AuthResponse, User } from '../types/api'

export interface RegisterPayload {
  email: string
  password: string
  first_name: string
  last_name?: string
}

export const authService = {
  async login(email: string, password: string): Promise<User> {
    const { data } = await api.post<AuthResponse>('/auth/login/', { email, password })
    setAccessToken(data.access)
    return data.user
  },

  async register(payload: RegisterPayload): Promise<User> {
    const { data } = await api.post<AuthResponse>('/auth/register/', payload)
    setAccessToken(data.access)
    return data.user
  },

  /** Restore a session from the HttpOnly refresh cookie (e.g. after reload). */
  async restoreSession(): Promise<User | null> {
    const token = await refreshAccessToken()
    if (!token) return null
    const { data } = await api.get<User>('/users/me/')
    return data
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout/')
    } finally {
      setAccessToken(null)
    }
  },
}
