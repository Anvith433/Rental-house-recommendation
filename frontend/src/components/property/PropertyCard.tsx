import { MapPin } from 'lucide-react'
import { Link } from 'react-router'
import type { PropertySummary } from '../../types/api'
import { availabilityLabel, formatRupees, PROPERTY_TYPE_LABELS } from '../../utils/format'
import { Skeleton } from '../ui/Feedback'
import { CompareToggle } from './CompareToggle'
import { FavoriteButton } from './FavoriteButton'
import { PropertyFacts } from './PropertyFacts'
import { PropertyImage } from './PropertyImage'

export function PropertyCard({ property }: { property: PropertySummary }) {
  return (
    <article className="group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="relative aspect-[4/3] overflow-hidden">
        <PropertyImage
          src={property.primary_image}
          alt={property.title}
          className="h-full w-full transition duration-300 group-hover:scale-[1.03]"
        />
        <span className="absolute left-3 top-3 rounded-full bg-white/95 px-2.5 py-1 text-xs font-medium text-slate-700 shadow-sm">
          {PROPERTY_TYPE_LABELS[property.property_type]}
        </span>
        <FavoriteButton propertyId={property.id} className="absolute right-3 top-3 z-10" />
      </div>
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div>
          <p className="text-lg font-semibold text-slate-900">
            {formatRupees(property.rent)}
            <span className="text-sm font-normal text-slate-500"> / month</span>
          </p>
          <h3 className="mt-1 line-clamp-1 text-sm font-medium text-slate-800">
            <Link to={`/properties/${property.id}`} className="after:absolute after:inset-0">
              {property.title}
            </Link>
          </h3>
          <p className="mt-1 flex items-center gap-1 text-sm text-slate-500">
            <MapPin className="h-3.5 w-3.5" aria-hidden />
            {property.location}, {property.city}
          </p>
        </div>
        <PropertyFacts property={property} compact />
        <div className="mt-auto flex items-center justify-between border-t border-slate-100 pt-3">
          <span className="text-xs text-slate-500">{availabilityLabel(property.available_from)}</span>
          <CompareToggle propertyId={property.id} className="relative z-10" />
        </div>
      </div>
    </article>
  )
}

export function PropertyCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <Skeleton className="aspect-[4/3] rounded-none" />
      <div className="space-y-3 p-4">
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </div>
  )
}

export function PropertyGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }, (_, index) => (
        <PropertyCardSkeleton key={index} />
      ))}
    </div>
  )
}
