import { ArrowRight, Clock, Heart, Search, Settings2, Sparkles } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { PageContainer } from '../components/layout/Page'
import { PropertyCard, PropertyCardSkeleton } from '../components/property/PropertyCard'
import { PreferenceSummary } from '../components/recommendation/PreferenceSummary'
import { Badge } from '../components/ui/Badge'
import { Button, ButtonLink } from '../components/ui/Button'
import { Card, CardHeader } from '../components/ui/Card'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/Feedback'
import { useAsync } from '../hooks/useAsync'
import { useAuth } from '../hooks/useAuth'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { favoriteService } from '../services/favoriteService'
import { userService } from '../services/userService'
import { formatDateTime, formatRupees } from '../utils/format'

function greeting() {
  const hour = new Date().getHours()
  return hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'
}

export function DashboardPage() {
  useDocumentTitle('Dashboard')
  const { user } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const favorites = useAsync(() => favoriteService.list(1, 3), [])
  const history = useAsync(() => userService.getHistory(1, 4), [])
  const preferences = useAsync(() => userService.getPreferences(), [])

  const quickSearch = (event: FormEvent) => {
    event.preventDefault()
    navigate(query.trim() ? `/properties?location=${encodeURIComponent(query.trim())}` : '/properties')
  }

  return (
    <PageContainer>
      <div className="mb-8 flex flex-col justify-between gap-6 rounded-3xl bg-gradient-to-br from-brand-800 to-brand-700 p-6 text-white sm:p-8 lg:flex-row lg:items-center">
        <div>
          <p className="text-sm text-brand-100">{greeting()},</p>
          <h1 className="mt-1 text-2xl font-semibold sm:text-3xl">{user?.first_name || 'there'} 👋</h1>
          <p className="mt-2 max-w-lg text-brand-100">Pick up where you left off, or start a fresh search.</p>
        </div>
        <form onSubmit={quickSearch} className="flex w-full max-w-md gap-2" role="search">
          <label className="relative flex-1">
            <span className="sr-only">Quick search by locality</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Quick search a locality"
              maxLength={100}
              className="h-11 w-full rounded-xl border-0 bg-white pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-white/60"
            />
          </label>
          <Button type="submit" className="h-11 bg-white !text-brand-800 hover:bg-brand-50">
            Search
          </Button>
        </form>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Heart className="h-4 w-4 text-rose-500" aria-hidden /> Saved properties
              </span>
            }
            action={
              <Link to="/favorites" className="text-sm font-medium text-brand-700 hover:text-brand-800">
                View all
              </Link>
            }
          />
          <div className="p-5">
            {favorites.loading ? (
              <div className="grid gap-4 sm:grid-cols-3">
                {[0, 1, 2].map((key) => (
                  <PropertyCardSkeleton key={key} />
                ))}
              </div>
            ) : favorites.error ? (
              <ErrorState error={favorites.error} onRetry={favorites.reload} />
            ) : favorites.data?.results.length ? (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {favorites.data.results.map((favorite) => (
                  <PropertyCard key={favorite.id} property={favorite.property} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<Heart className="h-6 w-6" aria-hidden />}
                title="No saved homes yet"
                description="Tap the heart on any listing to keep it here."
                action={<ButtonLink to="/properties" variant="secondary">Browse homes</ButtonLink>}
              />
            )}
          </div>
        </Card>

        <Card>
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Settings2 className="h-4 w-4 text-slate-500" aria-hidden /> Your preferences
              </span>
            }
            action={
              <Link to="/profile?tab=preferences" className="text-sm font-medium text-brand-700 hover:text-brand-800">
                Edit
              </Link>
            }
          />
          <div className="p-5">
            {preferences.loading ? (
              <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ) : preferences.error ? (
              <ErrorState error={preferences.error} onRetry={preferences.reload} />
            ) : preferences.data?.updated_at ? (
              <>
                <PreferenceSummary preferences={preferences.data} />
                <ButtonLink to="/recommendations" className="mt-5 w-full" icon={<Sparkles className="h-4 w-4" />}>
                  Get recommendations
                </ButtonLink>
              </>
            ) : (
              <div className="text-sm text-slate-500">
                <p>Save your preferences to get match scores on every listing.</p>
                <ButtonLink to="/recommendations" size="sm" className="mt-4">
                  Set preferences
                </ButtonLink>
              </div>
            )}
          </div>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-slate-500" aria-hidden /> Recent recommendations
              </span>
            }
            action={
              <Link to="/profile?tab=history" className="text-sm font-medium text-brand-700 hover:text-brand-800">
                Full history
              </Link>
            }
          />
          <div className="p-5">
            {history.loading ? (
              <div className="space-y-3">
                {[0, 1, 2].map((key) => (
                  <Skeleton key={key} className="h-14 w-full" />
                ))}
              </div>
            ) : history.error ? (
              <ErrorState error={history.error} onRetry={history.reload} />
            ) : history.data?.results.length ? (
              <ul className="divide-y divide-slate-100">
                {history.data.results.map((entry) => (
                  <li key={entry.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800">
                        {entry.request_preferences.location || 'Any location'}
                        {entry.request_preferences.max_rent ? ` · up to ${formatRupees(entry.request_preferences.max_rent)}` : ''}
                        {entry.request_preferences.bedrooms ? ` · ${entry.request_preferences.bedrooms} bed` : ''}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDateTime(entry.created_at)} · {entry.total_matches} matches
                        {entry.results[0] && (
                          <>
                            {' '}· top: <Link to={`/properties/${entry.results[0].id}`} className="text-brand-700 hover:underline">{entry.results[0].title}</Link>
                          </>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {entry.budget_relaxed && <Badge tone="warning">Budget relaxed</Badge>}
                      {entry.top_score !== null && <Badge tone="brand">Best {Math.round(entry.top_score)}%</Badge>}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                icon={<Sparkles className="h-6 w-6" aria-hidden />}
                title="No recommendation searches yet"
                action={
                  <ButtonLink to="/recommendations">
                    Find my homes <ArrowRight className="h-4 w-4" aria-hidden />
                  </ButtonLink>
                }
              />
            )}
          </div>
        </Card>
      </div>
    </PageContainer>
  )
}
