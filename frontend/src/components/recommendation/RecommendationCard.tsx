import { ArrowRight, MapPin } from 'lucide-react'
import { Link } from 'react-router'
import type { Recommendation } from '../../types/api'
import { formatRupees } from '../../utils/format'
import { CompareToggle } from '../property/CompareToggle'
import { FavoriteButton } from '../property/FavoriteButton'
import { PropertyFacts } from '../property/PropertyFacts'
import { PropertyImage } from '../property/PropertyImage'
import { ExplanationPanel } from './ExplanationPanel'
import { MatchScore } from './MatchScore'

export function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const { property, score, explanation, rank } = recommendation
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="grid md:grid-cols-[minmax(0,18rem)_1fr]">
        <div className="relative aspect-[4/3] md:aspect-auto">
          <PropertyImage src={property.primary_image} alt={property.title} className="h-full w-full" />
          <span className="absolute left-3 top-3 rounded-full bg-slate-900/80 px-2.5 py-1 text-xs font-semibold text-white">
            #{rank}
          </span>
        </div>
        <div className="flex flex-col gap-4 p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <h3 className="text-lg font-semibold text-slate-900">{property.title}</h3>
              <p className="mt-1 flex items-center gap-1 text-sm text-slate-500">
                <MapPin className="h-3.5 w-3.5" aria-hidden />
                {property.location}, {property.city}
              </p>
              <p className="mt-2 text-xl font-semibold text-slate-900">
                {formatRupees(property.rent)}
                <span className="text-sm font-normal text-slate-500"> / month</span>
              </p>
            </div>
            <MatchScore score={score} />
          </div>
          <PropertyFacts property={property} />
          <div className="rounded-xl bg-slate-50 p-4">
            <ExplanationPanel explanation={explanation} compact />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              to={`/properties/${property.id}`}
              state={{ recommendation }}
              className="inline-flex h-10 items-center gap-2 rounded-lg bg-brand-700 px-4 text-sm font-medium text-white shadow-sm hover:bg-brand-800"
            >
              View details
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
            <FavoriteButton propertyId={property.id} variant="full" />
            <CompareToggle propertyId={property.id} className="h-10 px-3" />
          </div>
        </div>
      </div>
    </article>
  )
}
