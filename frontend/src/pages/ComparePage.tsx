import { Check, GitCompareArrows, Minus, X } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { Page } from '../components/layout/Page'
import { PropertyImage } from '../components/property/PropertyImage'
import { Button, ButtonLink } from '../components/ui/Button'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/Feedback'
import { useAsync } from '../hooks/useAsync'
import { useAuth } from '../hooks/useAuth'
import { useCompare } from '../hooks/useCompare'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { propertyService } from '../services/propertyService'
import type { MatchEvaluation, Property } from '../types/api'
import { amenityLabel, availabilityLabel, bhkLabel, formatRupees, PROPERTY_TYPE_LABELS, scoreTone } from '../utils/format'

function YesNo({ value }: { value: boolean }) {
  return value ? (
    <span className="inline-flex items-center gap-1 text-emerald-700">
      <Check className="h-4 w-4" aria-hidden /> Yes
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-slate-400">
      <Minus className="h-4 w-4" aria-hidden /> No
    </span>
  )
}

interface Row {
  label: string
  render: (property: Property, match?: MatchEvaluation) => ReactNode
  best?: (properties: Property[]) => number | undefined
}

const ROWS: Row[] = [
  {
    label: 'Rent',
    render: (p) => <span className="font-semibold">{formatRupees(p.rent)}</span>,
    best: (ps) => ps.reduce((best, p) => (p.rent < ps[best].rent ? ps.indexOf(p) : best), 0),
  },
  { label: 'Deposit', render: (p) => formatRupees(p.security_deposit) },
  { label: 'Location', render: (p) => p.location },
  { label: 'Type', render: (p) => PROPERTY_TYPE_LABELS[p.property_type] },
  { label: 'Bedrooms', render: (p) => bhkLabel(p.bedrooms, p.property_type) },
  { label: 'Bathrooms', render: (p) => p.bathrooms },
  {
    label: 'Area',
    render: (p) => `${p.area_sqft.toLocaleString('en-IN')} sq ft`,
    best: (ps) => ps.reduce((best, p) => (p.area_sqft > ps[best].area_sqft ? ps.indexOf(p) : best), 0),
  },
  {
    label: 'Rent per sq ft',
    render: (p) => `₹${(p.rent / p.area_sqft).toFixed(1)}`,
    best: (ps) => ps.reduce((best, p) => (p.rent / p.area_sqft < ps[best].rent / ps[best].area_sqft ? ps.indexOf(p) : best), 0),
  },
  { label: 'Furnished', render: (p) => <YesNo value={p.furnished} /> },
  { label: 'Parking', render: (p) => <YesNo value={p.parking} /> },
  { label: 'Floor', render: (p) => (p.floor === null ? '—' : `${p.floor === 0 ? 'Ground' : p.floor} / ${p.total_floors ?? '—'}`) },
  { label: 'Availability', render: (p) => availabilityLabel(p.available_from) },
  {
    label: 'Amenities',
    render: (p) =>
      p.amenities.length ? (
        <span className="text-xs leading-relaxed text-slate-600">{p.amenities.map(amenityLabel).join(', ')}</span>
      ) : (
        '—'
      ),
  },
]

const SCORE_TEXT = { excellent: 'text-emerald-700', good: 'text-brand-800', fair: 'text-amber-700', low: 'text-slate-600' }

export function ComparePage() {
  useDocumentTitle('Compare homes')
  const { ids, remove, clear } = useCompare()
  const { user } = useAuth()
  const enough = ids.length >= 2
  const { data, error, loading, reload } = useAsync(
    () => (enough ? propertyService.compare(ids) : Promise.resolve(null)),
    [ids.join(','), user?.id],
  )

  if (!enough) {
    return (
      <Page title="Compare homes">
        <EmptyState
          icon={<GitCompareArrows className="h-6 w-6" aria-hidden />}
          title={ids.length === 1 ? 'Add one more home to compare' : 'Pick homes to compare'}
          description="Use the Compare button on any listing to add up to four homes, then come back here."
          action={<ButtonLink to="/properties">Browse homes</ButtonLink>}
        />
      </Page>
    )
  }

  const properties = data?.properties ?? []
  const matches = data?.matches ?? {}
  const hasMatches = Object.keys(matches).length > 0

  return (
    <Page
      title="Compare homes"
      description={hasMatches ? 'Match scores use your saved preferences.' : 'Save your preferences to add personal match scores.'}
      action={
        <Button variant="ghost" onClick={clear}>
          Clear all
        </Button>
      }
    >
      {loading ? (
        <Skeleton className="h-96 w-full rounded-2xl" />
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full min-w-[40rem] table-fixed text-sm">
            <caption className="sr-only">Side-by-side comparison of selected properties</caption>
            <thead>
              <tr>
                <th scope="col" className="sticky left-0 z-10 w-36 bg-white p-4 text-left align-bottom text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Property
                </th>
                {properties.map((property) => (
                  <th key={property.id} scope="col" className="p-4 text-left align-top font-normal">
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => remove(property.id)}
                        className="absolute right-1 top-1 z-10 rounded-full bg-white/90 p-1 text-slate-500 shadow hover:text-slate-800"
                        aria-label={`Remove ${property.title} from comparison`}
                      >
                        <X className="h-4 w-4" />
                      </button>
                      <PropertyImage src={property.primary_image} alt={property.title} className="aspect-[4/3] w-full rounded-xl" />
                      <Link to={`/properties/${property.id}`} className="mt-3 line-clamp-2 block font-semibold text-slate-900 hover:text-brand-700">
                        {property.title}
                      </Link>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {hasMatches && (
                <tr className="bg-brand-50/40">
                  <th scope="row" className="sticky left-0 z-10 bg-brand-50 p-4 text-left font-medium text-slate-700">
                    Match score
                  </th>
                  {properties.map((property) => {
                    const match = matches[String(property.id)]
                    return (
                      <td key={property.id} className="p-4">
                        {match ? (
                          <span className={`text-lg font-semibold ${SCORE_TEXT[scoreTone(match.score)]}`}>{Math.round(match.score)}%</span>
                        ) : (
                          '—'
                        )}
                      </td>
                    )
                  })}
                </tr>
              )}
              {ROWS.map((row) => {
                const best = row.best && properties.length > 1 ? row.best(properties) : undefined
                return (
                  <tr key={row.label}>
                    <th scope="row" className="sticky left-0 z-10 bg-white p-4 text-left font-medium text-slate-600">
                      {row.label}
                    </th>
                    {properties.map((property, index) => (
                      <td key={property.id} className={`p-4 align-top text-slate-800 ${best === index ? 'bg-emerald-50/70' : ''}`}>
                        {row.render(property, matches[String(property.id)])}
                        {best === index && <span className="ml-2 text-xs font-medium text-emerald-700">Best</span>}
                      </td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      {properties.length < ids.length && !loading && !error && (
        <p className="mt-4 text-sm text-slate-500">Some selected listings are no longer available and were skipped.</p>
      )}
    </Page>
  )
}
