import { ArrowRight, BadgeCheck, Check, GitCompareArrows, MapPin, Scale, Search, SlidersHorizontal, Sparkles, TrendingUp } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { PropertyCard, PropertyGridSkeleton } from '../components/property/PropertyCard'
import { ButtonLink } from '../components/ui/Button'
import { ErrorState } from '../components/ui/Feedback'
import { useAsync } from '../hooks/useAsync'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { propertyService } from '../services/propertyService'
import { SCORING_WEIGHTS } from '../utils/constants'
import { CRITERION_LABELS } from '../utils/format'
import type { Criterion } from '../types/api'

function HeroSearch() {
  const navigate = useNavigate()
  const [location, setLocation] = useState('')
  const [maxRent, setMaxRent] = useState('')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const params = new URLSearchParams()
    if (location.trim()) params.set('location', location.trim())
    if (maxRent) params.set('max_rent', maxRent)
    navigate(`/properties?${params.toString()}`)
  }

  return (
    <form
      onSubmit={submit}
      className="mt-8 flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-lg shadow-slate-200/60 sm:flex-row"
      role="search"
    >
      <label className="flex flex-1 items-center gap-2 rounded-xl px-3 py-2 focus-within:bg-slate-50">
        <MapPin className="h-5 w-5 shrink-0 text-brand-700" aria-hidden />
        <span className="sr-only">Location</span>
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Locality, e.g. Koramangala"
          className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
          maxLength={100}
        />
      </label>
      <label className="flex items-center gap-2 rounded-xl px-3 py-2 focus-within:bg-slate-50 sm:w-44 sm:border-l sm:border-slate-200">
        <span className="text-sm font-medium text-slate-400" aria-hidden>₹</span>
        <span className="sr-only">Maximum monthly rent</span>
        <input
          value={maxRent}
          onChange={(e) => setMaxRent(e.target.value.replace(/[^0-9]/g, ''))}
          placeholder="Max rent"
          inputMode="numeric"
          className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
        />
      </label>
      <button
        type="submit"
        className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-brand-700 px-5 text-sm font-medium text-white hover:bg-brand-800"
      >
        <Search className="h-4 w-4" aria-hidden />
        Search homes
      </button>
    </form>
  )
}

function HeroVisual() {
  return (
    <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
      <div className="grid grid-cols-5 grid-rows-2 gap-3">
        <img src="/images/properties/apartment-1.svg" alt="" className="col-span-3 row-span-2 h-full w-full rounded-2xl object-cover shadow-md" />
        <img src="/images/properties/living-2.svg" alt="" className="col-span-2 h-full w-full rounded-2xl object-cover shadow-md" />
        <img src="/images/properties/villa-3.svg" alt="" className="col-span-2 h-full w-full rounded-2xl object-cover shadow-md" />
      </div>
      <div className="absolute -bottom-6 left-4 right-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl sm:left-auto sm:right-6 sm:w-80">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-900">2 BHK near Agara Lake</p>
            <p className="text-xs text-slate-500">HSR Layout · ₹26,500/mo</p>
          </div>
          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-200">92%</span>
        </div>
        <ul className="mt-3 space-y-1.5 text-xs text-slate-600">
          {['Matches your preferred location', '₹3,500 below your budget', 'Furnished as requested'].map((line) => (
            <li key={line} className="flex items-center gap-1.5">
              <Check className="h-3.5 w-3.5 text-emerald-600" aria-hidden />
              {line}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

const STEPS = [
  {
    icon: SlidersHorizontal,
    title: 'Tell us what matters',
    body: 'Set your locality, budget, bedrooms and amenities — then mark each as must-have, important, preferred or optional.',
  },
  {
    icon: Sparkles,
    title: 'Get ranked matches',
    body: 'Every active listing that fits your hard requirements is scored on a transparent 100-point scale and ranked.',
  },
  {
    icon: BadgeCheck,
    title: 'See exactly why',
    body: 'Each recommendation lists what it gets right and where it falls short, so you can decide with confidence.',
  },
]

const REASONS = [
  { icon: Scale, title: 'Explainable, not a black box', body: 'Scores come from clear, published rules — never an opaque model. You can see the points behind every match.' },
  { icon: TrendingUp, title: 'Smart budget flexibility', body: "When nothing fits, we look slightly above your budget (up to 30%) — and tell you plainly that we did." },
  { icon: GitCompareArrows, title: 'Side-by-side comparison', body: 'Shortlist up to four homes and compare rent, space, amenities and match score in one view.' },
  { icon: BadgeCheck, title: 'Curated listings', body: 'Suspicious or outdated listings are flagged and removed by our team before they reach you.' },
]

export function LandingPage() {
  useDocumentTitle('')
  const featured = useAsync(() => propertyService.list({ page_size: 6, ordering: '-created_at' }), [])

  return (
    <>
      <section className="relative overflow-hidden bg-gradient-to-b from-brand-50/70 via-white to-white">
        <div className="mx-auto grid max-w-7xl items-center gap-16 px-4 pb-24 pt-14 sm:px-6 lg:grid-cols-2 lg:px-8 lg:pt-20">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-xs font-medium text-brand-800 ring-1 ring-brand-200">
              <Sparkles className="h-3.5 w-3.5" aria-hidden />
              Personalised rental recommendations for Bangalore
            </span>
            <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl lg:text-[3.4rem] lg:leading-[1.1]">
              Find a home that fits your life — and know <span className="text-brand-700">why</span> it fits.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-slate-600">
              RentWise ranks rentals against your priorities and explains every recommendation in plain language.
            </p>
            <HeroSearch />
            <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-500">
              <ButtonLink to="/recommendations" variant="ghost" className="-ml-3 text-brand-800">
                Build my personalised shortlist
                <ArrowRight className="h-4 w-4" aria-hidden />
              </ButtonLink>
            </div>
          </div>
          <HeroVisual />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Newly listed</h2>
            <p className="mt-1 text-slate-500">Fresh homes from across the city.</p>
          </div>
          <ButtonLink to="/properties" variant="secondary">
            View all homes
          </ButtonLink>
        </div>
        {featured.loading ? (
          <PropertyGridSkeleton count={6} />
        ) : featured.error ? (
          <ErrorState error={featured.error} onRetry={featured.reload} />
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {featured.data?.results.map((property) => <PropertyCard key={property.id} property={property} />)}
          </div>
        )}
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <h2 className="text-center text-2xl font-semibold tracking-tight text-slate-900">How it works</h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {STEPS.map((step, index) => (
              <div key={step.title} className="rounded-2xl border border-slate-200 p-6">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                    <step.icon className="h-5 w-5" aria-hidden />
                  </span>
                  <span className="text-sm font-medium text-slate-400">Step {index + 1}</span>
                </div>
                <h3 className="mt-4 font-semibold text-slate-900">{step.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{step.body}</p>
              </div>
            ))}
          </div>
          <div className="mx-auto mt-12 max-w-2xl rounded-2xl bg-slate-50 p-6">
            <p className="text-sm font-semibold text-slate-900">The 100-point scoring model</p>
            <div className="mt-4 space-y-2.5">
              {(Object.entries(SCORING_WEIGHTS) as [Criterion, number][]).map(([criterion, weight]) => (
                <div key={criterion} className="grid grid-cols-[6.5rem_1fr_2.5rem] items-center gap-3 text-sm">
                  <span className="text-slate-600">{CRITERION_LABELS[criterion]}</span>
                  <div className="h-2.5 overflow-hidden rounded-full bg-white ring-1 ring-slate-200">
                    <div className="h-full rounded-full bg-brand-600" style={{ width: `${(weight / 30) * 100}%` }} />
                  </div>
                  <span className="text-right font-medium tabular-nums text-slate-700">{weight}</span>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-slate-500">Your priorities scale each criterion from ×0.5 (optional) to ×1.5 (must-have).</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Why RentWise</h2>
        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          {REASONS.map((reason) => (
            <div key={reason.title} className="flex gap-4">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-700 text-white">
                <reason.icon className="h-5 w-5" aria-hidden />
              </span>
              <div>
                <h3 className="font-semibold text-slate-900">{reason.title}</h3>
                <p className="mt-1 text-sm text-slate-600">{reason.body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="px-4 pb-20 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 rounded-3xl bg-brand-800 px-8 py-12 sm:flex-row sm:items-center lg:px-12">
          <div>
            <h2 className="text-2xl font-semibold text-white">Ready to find your next home?</h2>
            <p className="mt-2 text-brand-100">Create a free account to save homes, keep your preferences and revisit past searches.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <ButtonLink to="/register" className="bg-white !text-brand-800 hover:bg-brand-50">
              Create free account
            </ButtonLink>
            <ButtonLink to="/recommendations" variant="ghost" className="text-white hover:bg-brand-700 hover:text-white">
              Try recommendations
            </ButtonLink>
          </div>
        </div>
      </section>
    </>
  )
}
