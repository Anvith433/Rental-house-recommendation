import { useEffect } from 'react'

export function useDocumentTitle(title: string) {
  useEffect(() => {
    document.title = title ? `${title} · RentWise` : 'RentWise – Smarter rental recommendations'
  }, [title])
}
