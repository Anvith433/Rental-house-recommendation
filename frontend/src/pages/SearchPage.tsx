import { Search, SlidersHorizontal, X } from 'lucide-react'
import { useMemo, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router'
import { Page } from '../components/layout/Page'
import { PropertyCard, PropertyGridSkeleton } from '../components/property/PropertyCard'
import { PropertyFiltersPanel } from '../components/property/PropertyFiltersPanel'
import { Button, ButtonLink } from '../components/ui/Button'
import { EmptyState, ErrorState } from '../components/ui/Feedback'
import { Select } from '../components/ui/Field'
import { Pagination } from '../components/ui/Pagination'
import { useAsync } from '../hooks/useAsync'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { propertyService } from '../services/propertyService'
import type { PropertyFilters, PropertyType } from '../types/api'
import { PAGE_SIZE } from '../utils/constants'

const SORT_OPTIONS = [
  { value: '-created_at', label: 'Newest first' },
  { value: 'rent', label: 'Rent: low to high' },
  { value: '-rent', label: 'Rent: high to low' },
  { value: '-area_sqft', label: 'Largest first' },
]

const NUMERIC_KEYS = ['min_rent', 'max_rent', 'bedrooms', 'bathrooms', 'page'] as const

function filtersFromParams(params: URLSearchParams): PropertyFilters {
  const filters: PropertyFilters = {}
  for (const key of NUMERIC_KEYS) {
    const value = params.get(key)
    if (value && !Number.isNaN(Number(value))) filters[key] = Number(value)
  }
  for (const key of ['furnished', 'parking'] as const) {
    const value = params.get(key)
    if (value === 'true' || value === 'false') filters[key] = value === 'true'
  }
  const location = params.get('location')
  if (location) filters.location = location
  const search = params.get('search')
  if (search) filters.search = search
  const type = params.get('property_type')
  if (type) filters.property_type = type as PropertyType
  filters.ordering = params.get('ordering') || '-created_at'
  return filters
}

function paramsFromFilters(filters: PropertyFilters): URLSearchParams {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === '') continue
    if (key === 'ordering' && value === '-created_at') continue
    if (key === 'page' && value === 1) continue
    params.set(key, String(value))
  }
  return params
}

export function SearchPage() {
  useDocumentTitle('Browse homes')
  const [params, setParams] = useSearchParams()
  const filters = useMemo(() => filtersFromParams(params), [params])
  const [query, setQuery] = useState(filters.search ?? '')
  const [drawerOpen, setDrawerOpen] = useState(false)

  const results = useAsync(() => propertyService.list({ ...filters, page_size: PAGE_SIZE }), [params.toString()])
  const locations = useAsync(() => propertyService.locations(), [])
  const locationNames = locations.data?.map((row) => row.location) ?? []

  const apply = (next: PropertyFilters) => {
    setParams(paramsFromFilters({ ...next, search: filters.search, ordering: filters.ordering, page: 1 }))
    setDrawerOpen(false)
  }
  const reset = () => {
    setQuery('')
    setParams(new URLSearchParams())
    setDrawerOpen(false)
  }
  const submitSearch = (event: FormEvent) => {
    event.preventDefault()
    setParams(paramsFromFilters({ ...filters, search: query.trim() || undefined, page: 1 }))
  }

  const activeCount = ['location', 'min_rent', 'max_rent', 'bedrooms', 'bathrooms', 'furnished', 'parking', 'property_type'].filter(
    (key) => params.has(key),
  ).length

  // Keyed by the URL so the draft form resets whenever the applied filters change.
  const filtersPanel = <PropertyFiltersPanel key={params.toString()} filters={filters} locations={locationNames} onApply={apply} onReset={reset} />

  return (
    <Page title="Browse homes" description="Search every active rental listing. Filters run on the server, so results are always current.">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <form onSubmit={submitSearch} className="relative flex-1" role="search">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by title, locality or description"
            aria-label="Search properties"
            maxLength={100}
            className="h-11 w-full rounded-xl border border-slate-300 bg-white pl-9 pr-24 text-sm shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/30"
          />
          <Button type="submit" size="sm" className="absolute right-1.5 top-1/2 -translate-y-1/2">
            Search
          </Button>
        </form>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            className="h-11 lg:hidden"
            onClick={() => setDrawerOpen(true)}
            icon={<SlidersHorizontal className="h-4 w-4" />}
          >
            Filters{activeCount > 0 && ` (${activeCount})`}
          </Button>
          <Select
            aria-label="Sort by"
            value={filters.ordering}
            onChange={(e) => setParams(paramsFromFilters({ ...filters, ordering: e.target.value, page: 1 }))}
            className="!h-11 min-w-44"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[17rem_1fr]">
        <aside className="hidden lg:block">
          <div className="sticky top-24 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold text-slate-900">Filters</h2>
            {filtersPanel}
          </div>
        </aside>

        <section aria-live="polite" aria-busy={results.loading}>
          {results.loading ? (
            <PropertyGridSkeleton count={6} />
          ) : results.error ? (
            <ErrorState error={results.error} onRetry={results.reload} />
          ) : results.data && results.data.results.length > 0 ? (
            <>
              <p className="mb-4 text-sm text-slate-500">
                {results.data.count} {results.data.count === 1 ? 'home' : 'homes'} found
              </p>
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {results.data.results.map((property) => (
                  <PropertyCard key={property.id} property={property} />
                ))}
              </div>
              <div className="mt-8">
                <Pagination
                  page={filters.page ?? 1}
                  pageSize={PAGE_SIZE}
                  total={results.data.count}
                  onChange={(page) => setParams(paramsFromFilters({ ...filters, page }))}
                />
              </div>
            </>
          ) : (
            <EmptyState
              title="No homes match these filters"
              description="Try widening your budget or removing a filter. Or let us rank the closest matches for you."
              action={
                <div className="flex flex-wrap justify-center gap-2">
                  <Button variant="secondary" onClick={reset}>
                    Clear filters
                  </Button>
                  <ButtonLink to="/recommendations">Get recommendations</ButtonLink>
                </div>
              }
            />
          )}
        </section>
      </div>

      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Filters">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setDrawerOpen(false)} />
          <div className="absolute inset-y-0 right-0 w-full max-w-sm overflow-y-auto bg-white p-5 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900">Filters</h2>
              <button type="button" onClick={() => setDrawerOpen(false)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100" aria-label="Close filters">
                <X className="h-5 w-5" />
              </button>
            </div>
            {filtersPanel}
          </div>
        </div>
      )}
    </Page>
  )
}
