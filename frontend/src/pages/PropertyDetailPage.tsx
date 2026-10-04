import {
  ArrowLeft,
  Bath,
  BedDouble,
  Building2,
  CalendarDays,
  Car,
  Check,
  Layers,
  MapPin,
  Maximize,
  MessageSquare,
  Sofa,
  Wallet,
} from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router'
import { PageContainer } from '../components/layout/Page'
import { CompareToggle } from '../components/property/CompareToggle'
import { FavoriteButton } from '../components/property/FavoriteButton'
import { PropertyImage } from '../components/property/PropertyImage'
import { ExplanationPanel } from '../components/recommendation/ExplanationPanel'
import { MatchScore } from '../components/recommendation/MatchScore'
import { Badge } from '../components/ui/Badge'
import { Button, ButtonLink } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { ErrorState, Skeleton } from '../components/ui/Feedback'
import { Input, Textarea } from '../components/ui/Field'
import { Modal } from '../components/ui/Modal'
import { useAsync } from '../hooks/useAsync'
import { useAuth } from '../hooks/useAuth'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { useToast } from '../hooks/useToast'
import { propertyService } from '../services/propertyService'
import type { MatchEvaluation, PropertyDetail, Recommendation } from '../types/api'
import { toAppError } from '../utils/errors'
import { amenityLabel, availabilityLabel, bhkLabel, formatRupees, PROPERTY_TYPE_LABELS } from '../utils/format'

function Gallery({ property }: { property: PropertyDetail }) {
  const images = property.images.length ? property.images : [{ image_url: property.primary_image ?? '', caption: '', is_primary: true }]
  const [active, setActive] = useState(0)
  const current = images[Math.min(active, images.length - 1)]
  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <PropertyImage src={current.image_url} alt={current.caption || property.title} className="aspect-[16/10] w-full" />
      </div>
      {images.length > 1 && (
        <div className="grid grid-cols-4 gap-3">
          {images.map((image, index) => (
            <button
              key={`${image.image_url}-${index}`}
              type="button"
              onClick={() => setActive(index)}
              aria-label={`Show image ${index + 1}${image.caption ? `: ${image.caption}` : ''}`}
              aria-current={index === active}
              className={`overflow-hidden rounded-xl border-2 transition ${index === active ? 'border-brand-600' : 'border-transparent opacity-80 hover:opacity-100'}`}
            >
              <PropertyImage src={image.image_url} alt="" className="aspect-[4/3] w-full" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function InquiryModal({ property, open, onClose }: { property: PropertyDetail; open: boolean; onClose: () => void }) {
  const { notify } = useToast()
  const [message, setMessage] = useState(`Hi, I'm interested in "${property.title}". Is it still available?`)
  const [phone, setPhone] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (message.trim().length < 10) {
      setErrors({ message: 'Please write at least 10 characters.' })
      return
    }
    setLoading(true)
    try {
      await propertyService.inquire(property.id, message.trim(), phone.trim())
      notify('Your request was sent. The listing team will get back to you.', 'success')
      onClose()
    } catch (error) {
      const appError = toAppError(error)
      setErrors(appError.fieldErrors)
      if (!Object.keys(appError.fieldErrors).length) notify(appError.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Request information"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="inquiry-form" loading={loading}>
            Send request
          </Button>
        </>
      }
    >
      <form id="inquiry-form" onSubmit={submit} className="space-y-4" noValidate>
        <Textarea label="Message" rows={4} value={message} onChange={(e) => setMessage(e.target.value)} maxLength={2000} error={errors.message} />
        <Input label="Phone (optional)" type="tel" autoComplete="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 98xxx xxxxx" error={errors.phone} />
      </form>
    </Modal>
  )
}

function DetailSkeleton() {
  return (
    <PageContainer>
      <Skeleton className="mb-6 h-5 w-32" />
      <div className="grid gap-8 lg:grid-cols-[1fr_22rem]">
        <div className="space-y-4">
          <Skeleton className="aspect-[16/10] w-full rounded-2xl" />
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-32 w-full" />
        </div>
        <Skeleton className="h-72 w-full rounded-2xl" />
      </div>
    </PageContainer>
  )
}

export function PropertyDetailPage() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [inquiryOpen, setInquiryOpen] = useState(false)
  const fromRecommendation = (location.state as { recommendation?: Recommendation } | null)?.recommendation
  const { data: property, error, loading, reload } = useAsync(() => propertyService.get(id ?? ''), [id])
  useDocumentTitle(property?.title ?? 'Property')

  if (loading) return <DetailSkeleton />
  if (error || !property)
    return (
      <PageContainer>
        <ErrorState error={error ?? { kind: 'not_found', message: 'This property is no longer available.', fieldErrors: {} }} onRetry={reload} />
        <div className="mt-6 text-center">
          <ButtonLink to="/properties" variant="secondary">
            Back to all homes
          </ButtonLink>
        </div>
      </PageContainer>
    )

  const match: MatchEvaluation | undefined = fromRecommendation ?? property.match
  const facts = [
    { icon: BedDouble, label: 'Bedrooms', value: bhkLabel(property.bedrooms, property.property_type) },
    { icon: Bath, label: 'Bathrooms', value: property.bathrooms },
    { icon: Maximize, label: 'Area', value: `${property.area_sqft.toLocaleString('en-IN')} sq ft` },
    { icon: Sofa, label: 'Furnishing', value: property.furnished ? 'Furnished' : 'Unfurnished' },
    { icon: Car, label: 'Parking', value: property.parking ? 'Available' : 'Not available' },
    { icon: Building2, label: 'Type', value: PROPERTY_TYPE_LABELS[property.property_type] },
    {
      icon: Layers,
      label: 'Floor',
      value: property.floor === null ? '—' : property.floor === 0 ? `Ground of ${property.total_floors ?? '—'}` : `${property.floor} of ${property.total_floors ?? '—'}`,
    },
    { icon: CalendarDays, label: 'Availability', value: availabilityLabel(property.available_from) },
  ]

  return (
    <PageContainer>
      <button
        type="button"
        onClick={() => (location.key === 'default' ? navigate('/properties') : navigate(-1))}
        className="mb-6 inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden /> Back
      </button>

      <div className="grid gap-8 lg:grid-cols-[1fr_22rem]">
        <div className="min-w-0 space-y-8">
          <Gallery property={property} />

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="brand">{PROPERTY_TYPE_LABELS[property.property_type]}</Badge>
              {property.status !== 'active' && <Badge tone="warning">{property.status}</Badge>}
            </div>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">{property.title}</h1>
            <p className="mt-2 flex items-center gap-1.5 text-slate-500">
              <MapPin className="h-4 w-4" aria-hidden />
              {property.location}, {property.city}, {property.state}
            </p>
          </div>

          <Card className="p-5">
            <h2 className="mb-4 text-base font-semibold text-slate-900">Key details</h2>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-4">
              {facts.map((fact) => (
                <div key={fact.label}>
                  <dt className="flex items-center gap-1.5 text-xs text-slate-500">
                    <fact.icon className="h-3.5 w-3.5" aria-hidden />
                    {fact.label}
                  </dt>
                  <dd className="mt-1 text-sm font-medium text-slate-900">{fact.value}</dd>
                </div>
              ))}
            </dl>
          </Card>

          {property.description && (
            <section>
              <h2 className="mb-2 text-base font-semibold text-slate-900">About this home</h2>
              {/* Rendered as text (never HTML) so listing content cannot inject markup. */}
              <p className="whitespace-pre-line text-sm leading-relaxed text-slate-600">{property.description}</p>
            </section>
          )}

          {property.amenities.length > 0 && (
            <section>
              <h2 className="mb-3 text-base font-semibold text-slate-900">Amenities</h2>
              <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {property.amenities.map((amenity) => (
                  <li key={amenity} className="flex items-center gap-2 text-sm text-slate-700">
                    <Check className="h-4 w-4 text-brand-600" aria-hidden />
                    {amenityLabel(amenity)}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <aside className="space-y-5 lg:sticky lg:top-24 lg:self-start">
          <Card className="p-5">
            <p className="text-2xl font-semibold text-slate-900">
              {formatRupees(property.rent)}
              <span className="text-sm font-normal text-slate-500"> / month</span>
            </p>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-500">
              <Wallet className="h-4 w-4" aria-hidden />
              Deposit {formatRupees(property.security_deposit)}
            </p>
            <div className="mt-5 grid gap-2">
              {user ? (
                <Button onClick={() => setInquiryOpen(true)} icon={<MessageSquare className="h-4 w-4" />}>
                  Request information
                </Button>
              ) : (
                <ButtonLink to="/login" state={{ from: location.pathname }} icon={<MessageSquare className="h-4 w-4" />}>
                  Sign in to contact
                </ButtonLink>
              )}
              <div className="grid grid-cols-2 gap-2">
                <FavoriteButton propertyId={property.id} variant="full" />
                <CompareToggle propertyId={property.id} className="h-10 justify-center" />
              </div>
            </div>
          </Card>

          {match ? (
            <Card className="p-5">
              <h2 className="mb-4 text-base font-semibold text-slate-900">Why we recommend this</h2>
              <MatchScore score={match.score} size="lg" />
              <div className="mt-5">
                <ExplanationPanel explanation={match.explanation} breakdown={match.score_breakdown} />
              </div>
              {!fromRecommendation && <p className="mt-4 text-xs text-slate-400">Based on your saved preferences.</p>}
            </Card>
          ) : (
            <Card className="p-5">
              <h2 className="text-base font-semibold text-slate-900">How well does it fit you?</h2>
              <p className="mt-1 text-sm text-slate-500">
                {user ? 'Save your preferences to see a personal match score here.' : 'Sign in and save your preferences to see a personal match score.'}
              </p>
              <ButtonLink to={user ? '/profile?tab=preferences' : '/login'} variant="outline" size="sm" className="mt-4">
                {user ? 'Set preferences' : 'Sign in'}
              </ButtonLink>
            </Card>
          )}
        </aside>
      </div>

      {user && <InquiryModal property={property} open={inquiryOpen} onClose={() => setInquiryOpen(false)} />}
    </PageContainer>
  )
}
