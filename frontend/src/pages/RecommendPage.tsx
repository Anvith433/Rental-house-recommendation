import { Compass, Sparkles } from 'lucide-react'
import { useRef, useState } from 'react'
import { PageContainer, PageHeader } from '../components/layout/Page'
import { BudgetRelaxationNotice } from '../components/recommendation/BudgetRelaxationNotice'
import { PreferenceForm } from '../components/recommendation/PreferenceForm'
import { RecommendationCard } from '../components/recommendation/RecommendationCard'
import { Card } from '../components/ui/Card'
import { Alert, EmptyState, ErrorState, Skeleton, Spinner } from '../components/ui/Feedback'
import { Checkbox, Select } from '../components/ui/Field'
import { useAsync } from '../hooks/useAsync'
import { useAuth } from '../hooks/useAuth'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { useToast } from '../hooks/useToast'
import { propertyService } from '../services/propertyService'
import { recommendationService } from '../services/recommendationService'
import { userService } from '../services/userService'
import type { Preferences, RecommendationResponse } from '../types/api'
import { toAppError, type AppError } from '../utils/errors'

const LAST_RESULT_KEY = 'rentwise.lastRecommendation'

interface StoredResult {
  preferences: Preferences
  response: RecommendationResponse
}

function loadLastResult(): StoredResult | null {
  try {
    const raw = sessionStorage.getItem(LAST_RESULT_KEY)
    return raw ? (JSON.parse(raw) as StoredResult) : null
  } catch {
    return null
  }
}

function ResultsSkeleton() {
  return (
    <div className="space-y-4">
      {[0, 1, 2].map((key) => (
        <div key={key} className="grid overflow-hidden rounded-2xl border border-slate-200 bg-white md:grid-cols-[18rem_1fr]">
          <Skeleton className="aspect-[4/3] rounded-none md:aspect-auto md:h-64" />
          <div className="space-y-3 p-5">
            <Skeleton className="h-6 w-2/3" />
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-10 w-48" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function RecommendPage() {
  useDocumentTitle('Recommendations')
  const { user, status } = useAuth()
  const { notify } = useToast()
  const [stored] = useState(loadLastResult)
  const [result, setResult] = useState<RecommendationResponse | null>(stored?.response ?? null)
  const [lastPreferences, setLastPreferences] = useState<Preferences | undefined>(stored?.preferences)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<AppError | null>(null)
  const [topN, setTopN] = useState(String(stored?.response.requested_top_n ?? 10))
  const [saveChoice, setSavePreferences] = useState<boolean | null>(null)
  const resultsRef = useRef<HTMLDivElement>(null)

  const locations = useAsync(() => propertyService.locations(), [])
  const saved = useAsync(
    () => (status === 'authenticated' ? userService.getPreferences() : Promise.resolve(null)),
    [status],
  )

  // Default to saving when the user has no saved preferences yet.
  const savePreferences = saveChoice ?? Boolean(saved.data && !saved.data.updated_at)

  const initial = lastPreferences ?? (saved.data?.updated_at ? saved.data : undefined)

  const run = async (preferences: Preferences) => {
    setLoading(true)
    setError(null)
    setLastPreferences(preferences)
    try {
      const response = await recommendationService.recommend({ ...preferences, top_n: Number(topN) })
      setResult(response)
      try {
        sessionStorage.setItem(LAST_RESULT_KEY, JSON.stringify({ preferences, response }))
      } catch {
        // Non-essential convenience; ignore storage failures.
      }
      if (user && savePreferences) {
        await userService.savePreferences(preferences)
        notify('Preferences saved to your profile.', 'success')
      }
      if (window.innerWidth < 1024) resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } catch (caught) {
      setError(toAppError(caught))
    } finally {
      setLoading(false)
    }
  }

  const formReady = status !== 'loading' && !saved.loading

  return (
    <PageContainer>
      <PageHeader
        title="Find your best-fit homes"
        description="Tell us what you need and how much each thing matters. We'll rank every matching listing and explain each result."
      />
      <div className="grid gap-8 lg:grid-cols-[26rem_1fr]">
        <Card className="h-fit p-5 lg:sticky lg:top-24">
          {formReady ? (
            <PreferenceForm
              key={initial ? 'with-initial' : 'blank'}
              initial={initial}
              onSubmit={run}
              submitLabel="Find my homes"
              loading={loading}
              serverErrors={error?.fieldErrors}
              locations={locations.data?.map((row) => row.location)}
              footer={
                <div className="space-y-3 border-t border-slate-100 pt-5">
                  <Select label="Number of results" value={topN} onChange={(e) => setTopN(e.target.value)}>
                    {[5, 10, 20].map((n) => (
                      <option key={n} value={n}>
                        Top {n}
                      </option>
                    ))}
                  </Select>
                  {user && (
                    <Checkbox
                      label="Save as my preferences"
                      description="Used for match scores across the site."
                      checked={savePreferences}
                      onChange={(e) => setSavePreferences(e.target.checked)}
                    />
                  )}
                </div>
              }
            />
          ) : (
            <Spinner label="Loading your preferences" />
          )}
        </Card>

        <div ref={resultsRef} className="min-w-0 scroll-mt-24" aria-live="polite" aria-busy={loading}>
          {loading ? (
            <ResultsSkeleton />
          ) : error && !Object.keys(error.fieldErrors).length ? (
            <ErrorState error={error} />
          ) : result ? (
            <div className="space-y-5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="text-xl font-semibold text-slate-900">Top recommendations</h2>
                <p className="text-sm text-slate-500">
                  {result.total_matches} {result.total_matches === 1 ? 'home meets' : 'homes meet'} your requirements · showing{' '}
                  {result.returned_count}
                </p>
              </div>
              {error && <Alert tone="error">{error.message}</Alert>}
              <BudgetRelaxationNotice response={result} />
              {result.recommendations.length > 0 ? (
                result.recommendations.map((recommendation) => (
                  <RecommendationCard key={recommendation.property.id} recommendation={recommendation} />
                ))
              ) : (
                <EmptyState
                  icon={<Compass className="h-6 w-6" aria-hidden />}
                  title="No homes match all of your hard requirements"
                  description="Hard requirements are your location, budget range, bedroom count and required parking. Try a nearby locality, a wider budget, or the 'at least' bedroom option."
                />
              )}
            </div>
          ) : (
            <div className="flex h-full min-h-80 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
                <Sparkles className="h-7 w-7" aria-hidden />
              </span>
              <h2 className="mt-4 text-lg font-semibold text-slate-900">Your shortlist will appear here</h2>
              <p className="mt-1 max-w-md text-sm text-slate-500">
                Homes are first filtered by your hard requirements, then scored out of 100 on location, budget, bedrooms, furnishing and parking —
                weighted by your priorities.
              </p>
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  )
}
