import { useContext } from 'react'
import { CompareContext } from '../context/contexts'

export function useCompare() {
  const context = useContext(CompareContext)
  if (!context) throw new Error('useCompare must be used inside its provider')
  return context
}
