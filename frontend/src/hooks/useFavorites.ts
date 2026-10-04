import { useContext } from 'react'
import { FavoritesContext } from '../context/contexts'

export function useFavorites() {
  const context = useContext(FavoritesContext)
  if (!context) throw new Error('useFavorites must be used inside its provider')
  return context
}
