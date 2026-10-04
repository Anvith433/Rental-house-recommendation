import { GitCompareArrows, Heart, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'
import { Page } from '../components/layout/Page'
import { PropertyFacts } from '../components/property/PropertyFacts'
import { PropertyGridSkeleton } from '../components/property/PropertyCard'
import { PropertyImage } from '../components/property/PropertyImage'
import { Button, ButtonLink } from '../components/ui/Button'
import { EmptyState, ErrorState } from '../components/ui/Feedback'
import { Pagination } from '../components/ui/Pagination'
import { useAsync } from '../hooks/useAsync'
import { useCompare } from '../hooks/useCompare'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { useFavorites } from '../hooks/useFavorites'
import { favoriteService } from '../services/favoriteService'
import { formatDate, formatRupees } from '../utils/format'

const PAGE_SIZE = 12

export function FavoritesPage() {
  useDocumentTitle('Saved properties')
  const [page, setPage] = useState(1)
  const { toggle } = useFavorites()
  const { has, toggle: toggleCompare, isFull } = useCompare()
  const { data, error, loading, reload, setData } = useAsync(() => favoriteService.list(page, PAGE_SIZE), [page])

  const remove = async (propertyId: number) => {
    await toggle(propertyId)
    setData((current) =>
      current
        ? { ...current, count: current.count - 1, results: current.results.filter((f) => f.property.id !== propertyId) }
        : current,
    )
  }

  return (
    <Page
      title="Saved properties"
      description="Homes you've shortlisted. Select two to four to compare side by side."
      action={
        <ButtonLink to="/compare" variant="secondary" icon={<GitCompareArrows className="h-4 w-4" />}>
          Open comparison
        </ButtonLink>
      }
    >
      {loading ? (
        <PropertyGridSkeleton count={3} />
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : !data?.results.length ? (
        <EmptyState
          icon={<Heart className="h-6 w-6" aria-hidden />}
          title="You haven't saved any homes yet"
          description="Save homes while browsing or from your recommendations, and they'll appear here."
          action={<ButtonLink to="/properties">Browse homes</ButtonLink>}
        />
      ) : (
        <>
          <ul className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {data.results.map(({ id, property, created_at }) => (
              <li key={id} className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <Link to={`/properties/${property.id}`} className="block">
                  <PropertyImage src={property.primary_image} alt={property.title} className="aspect-[16/10] w-full" />
                </Link>
                <div className="flex flex-1 flex-col gap-3 p-4">
                  <div>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatRupees(property.rent)}
                      <span className="text-sm font-normal text-slate-500"> / month</span>
                    </p>
                    <Link to={`/properties/${property.id}`} className="line-clamp-1 text-sm font-medium text-slate-800 hover:text-brand-700">
                      {property.title}
                    </Link>
                    <p className="text-sm text-slate-500">{property.location}</p>
                  </div>
                  <PropertyFacts property={property} compact />
                  {property.status !== 'active' && (
                    <p className="text-xs font-medium text-amber-700">This listing is no longer active.</p>
                  )}
                  <p className="text-xs text-slate-400">Saved {formatDate(created_at)}</p>
                  <div className="mt-auto grid grid-cols-3 gap-2 border-t border-slate-100 pt-3">
                    <ButtonLink to={`/properties/${property.id}`} variant="secondary" size="sm">
                      Details
                    </ButtonLink>
                    <Button
                      variant={has(property.id) ? 'primary' : 'secondary'}
                      size="sm"
                      onClick={() => toggleCompare(property.id)}
                      disabled={!has(property.id) && isFull}
                      aria-pressed={has(property.id)}
                    >
                      {has(property.id) ? 'Comparing' : 'Compare'}
                    </Button>
                    <Button variant="ghost" size="sm" className="text-rose-600 hover:bg-rose-50 hover:text-rose-700" onClick={() => remove(property.id)} icon={<Trash2 className="h-4 w-4" />}>
                      Remove
                    </Button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-8">
            <Pagination page={page} pageSize={PAGE_SIZE} total={data.count} onChange={setPage} />
          </div>
        </>
      )}
    </Page>
  )
}
