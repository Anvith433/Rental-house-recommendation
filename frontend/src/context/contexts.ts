import { createContext } from 'react'
import type { User } from '../types/api'
import type { RegisterPayload } from '../services/authService'

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

export interface AuthContextValue {
  user: User | null
  status: AuthStatus
  login: (email: string, password: string) => Promise<User>
  register: (payload: RegisterPayload) => Promise<User>
  logout: () => Promise<void>
  setUser: (user: User) => void
}

export interface FavoritesContextValue {
  ids: Set<number>
  isFavorite: (id: number) => boolean
  toggle: (id: number) => Promise<void>
  pending: Set<number>
}

export interface CompareContextValue {
  ids: number[]
  has: (id: number) => boolean
  toggle: (id: number) => void
  remove: (id: number) => void
  clear: () => void
  isFull: boolean
}

export type ToastTone = 'success' | 'error' | 'info'

export interface Toast {
  id: number
  message: string
  tone: ToastTone
}

export interface ToastContextValue {
  notify: (message: string, tone?: ToastTone) => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
export const FavoritesContext = createContext<FavoritesContextValue | null>(null)
export const CompareContext = createContext<CompareContextValue | null>(null)
export const ToastContext = createContext<ToastContextValue | null>(null)
