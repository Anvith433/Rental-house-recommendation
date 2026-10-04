import { Home } from 'lucide-react'
import { useState } from 'react'

interface PropertyImageProps {
  src: string | null | undefined
  alt: string
  className?: string
}

/** Image with a graceful placeholder when the URL is missing or fails to load. */
export function PropertyImage({ src, alt, className = '' }: PropertyImageProps) {
  const [failedSrc, setFailedSrc] = useState<string | null>(null)
  if (!src || failedSrc === src) {
    return (
      <div
        className={`flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 text-slate-400 ${className}`}
        role="img"
        aria-label={`${alt} (image unavailable)`}
      >
        <Home className="h-10 w-10" aria-hidden />
      </div>
    )
  }
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      decoding="async"
      onError={() => setFailedSrc(src)}
      className={`object-cover ${className}`}
    />
  )
}
