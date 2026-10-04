import { useContext } from 'react'
import { AuthContext } from '../context/contexts'

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside its provider')
  return context
}
