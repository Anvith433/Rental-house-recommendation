import { Plus, Trash2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useToast } from '../../hooks/useToast'
import { propertyService, type PropertyInput } from '../../services/propertyService'
import type { ListingStatus, Property, PropertyImage, PropertyType } from '../../types/api'
import { AMENITIES, PROPERTY_TYPES } from '../../utils/constants'
import { toAppError } from '../../utils/errors'
import { amenityLabel, PROPERTY_TYPE_LABELS } from '../../utils/format'
import { Button } from '../ui/Button'
import { Checkbox, Input, Select, Textarea } from '../ui/Field'
import { Modal } from '../ui/Modal'

interface Props {
  open: boolean
  property: Property | null
  onClose: () => void
  onSaved: () => void
}

interface FormState {
  title: string
  description: string
  location: string
  city: string
  state: string
  rent: string
  security_deposit: string
  bedrooms: string
  bathrooms: string
  area_sqft: string
  property_type: PropertyType
  floor: string
  total_floors: string
  available_from: string
  furnished: boolean
  parking: boolean
  status: ListingStatus
  amenities: string[]
  images: PropertyImage[]
}

function initialState(property: Property | null): FormState {
  const str = (value: number | string | null | undefined) => (value === null || value === undefined ? '' : String(value))
  return {
    title: property?.title ?? '',
    description: property?.description ?? '',
    location: property?.location ?? '',
    city: property?.city ?? 'Bangalore',
    state: property?.state ?? 'Karnataka',
    rent: str(property?.rent),
    security_deposit: str(property?.security_deposit ?? 0),
    bedrooms: str(property?.bedrooms ?? 2),
    bathrooms: str(property?.bathrooms ?? 2),
    area_sqft: str(property?.area_sqft),
    property_type: property?.property_type ?? 'apartment',
    floor: str(property?.floor),
    total_floors: str(property?.total_floors),
    available_from: property?.available_from ?? '',
    furnished: property?.furnished ?? false,
    parking: property?.parking ?? false,
    status: property?.status ?? 'active',
    amenities: property?.amenities ?? [],
    images: property?.images.length ? property.images : [{ image_url: '', caption: 'Exterior', is_primary: true }],
  }
}

function toPayload(state: FormState): Partial<PropertyInput> {
  const num = (value: string) => (value === '' ? null : Number(value))
  return {
    title: state.title.trim(),
    description: state.description.trim(),
    location: state.location.trim(),
    city: state.city.trim(),
    state: state.state.trim(),
    rent: Number(state.rent),
    security_deposit: Number(state.security_deposit || 0),
    bedrooms: Number(state.bedrooms),
    bathrooms: Number(state.bathrooms),
    area_sqft: Number(state.area_sqft),
    property_type: state.property_type,
    floor: num(state.floor),
    total_floors: num(state.total_floors),
    available_from: state.available_from || null,
    furnished: state.furnished,
    parking: state.parking,
    status: state.status,
    amenities: state.amenities,
    images: state.images
      .filter((image) => image.image_url.trim())
      .map((image) => ({ image_url: image.image_url.trim(), caption: image.caption, is_primary: image.is_primary })),
  }
}

export function PropertyFormModal({ open, property, onClose, onSaved }: Props) {
  const { notify } = useToast()
  const [state, setState] = useState<FormState>(() => initialState(property))
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setState((s) => ({ ...s, [key]: value }))
  const text = (key: keyof FormState) => (event: { target: { value: string } }) => set(key, event.target.value as never)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const found: Record<string, string> = {}
    if (state.title.trim().length < 5) found.title = 'Title must be at least 5 characters.'
    if (!state.location.trim()) found.location = 'Location is required.'
    if (!state.rent || Number(state.rent) < 0) found.rent = 'Enter a valid rent.'
    if (!state.area_sqft || Number(state.area_sqft) < 50) found.area_sqft = 'Area must be at least 50 sq ft.'
    setErrors(found)
    if (Object.keys(found).length) return

    setSaving(true)
    try {
      if (property) await propertyService.update(property.id, toPayload(state))
      else await propertyService.create(toPayload(state))
      notify(property ? 'Listing updated.' : 'Listing created.', 'success')
      onSaved()
    } catch (error) {
      const appError = toAppError(error)
      setErrors(appError.fieldErrors)
      notify(appError.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const updateImage = (index: number, patch: Partial<PropertyImage>) =>
    set(
      'images',
      state.images.map((image, i) =>
        i === index ? { ...image, ...patch } : patch.is_primary ? { ...image, is_primary: false } : image,
      ),
    )

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="xl"
      title={property ? 'Edit listing' : 'New listing'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" form="property-form" loading={saving}>
            {property ? 'Save changes' : 'Create listing'}
          </Button>
        </>
      }
    >
      <form id="property-form" onSubmit={submit} noValidate className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Title" value={state.title} onChange={text('title')} error={errors.title} containerClassName="sm:col-span-2" maxLength={200} />
          <Textarea label="Description" rows={3} value={state.description} onChange={text('description')} error={errors.description} containerClassName="sm:col-span-2" />
          <Input label="Locality" value={state.location} onChange={text('location')} error={errors.location} placeholder="e.g. HSR Layout" />
          <div className="grid grid-cols-2 gap-3">
            <Input label="City" value={state.city} onChange={text('city')} error={errors.city} />
            <Input label="State" value={state.state} onChange={text('state')} error={errors.state} />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-4">
          <Input label="Rent (₹/month)" type="number" min={0} value={state.rent} onChange={text('rent')} error={errors.rent} />
          <Input label="Deposit (₹)" type="number" min={0} value={state.security_deposit} onChange={text('security_deposit')} error={errors.security_deposit} />
          <Input label="Area (sq ft)" type="number" min={50} value={state.area_sqft} onChange={text('area_sqft')} error={errors.area_sqft} />
          <Select label="Type" value={state.property_type} onChange={text('property_type')} error={errors.property_type}>
            {PROPERTY_TYPES.map((type) => (
              <option key={type} value={type}>
                {PROPERTY_TYPE_LABELS[type]}
              </option>
            ))}
          </Select>
          <Input label="Bedrooms" type="number" min={0} max={20} value={state.bedrooms} onChange={text('bedrooms')} error={errors.bedrooms} />
          <Input label="Bathrooms" type="number" min={0} max={20} value={state.bathrooms} onChange={text('bathrooms')} error={errors.bathrooms} />
          <Input label="Floor" type="number" value={state.floor} onChange={text('floor')} error={errors.floor} />
          <Input label="Total floors" type="number" min={1} value={state.total_floors} onChange={text('total_floors')} error={errors.total_floors} />
          <Input label="Available from" type="date" value={state.available_from} onChange={text('available_from')} error={errors.available_from} />
          <Select label="Status" value={state.status} onChange={text('status')} error={errors.status}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="flagged">Flagged for review</option>
          </Select>
          <div className="flex flex-col justify-end gap-2 sm:col-span-2">
            <Checkbox label="Furnished" checked={state.furnished} onChange={(e) => set('furnished', e.target.checked)} />
            <Checkbox label="Parking available" checked={state.parking} onChange={(e) => set('parking', e.target.checked)} />
          </div>
        </div>
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-700">Amenities</legend>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {AMENITIES.map((amenity) => (
              <Checkbox
                key={amenity}
                label={amenityLabel(amenity)}
                checked={state.amenities.includes(amenity)}
                onChange={(e) =>
                  set('amenities', e.target.checked ? [...state.amenities, amenity] : state.amenities.filter((a) => a !== amenity))
                }
              />
            ))}
          </div>
          {errors.amenities && <p className="mt-1 text-xs text-rose-600">{errors.amenities}</p>}
        </fieldset>
        <fieldset>
          <legend className="mb-2 text-sm font-medium text-slate-700">Images</legend>
          <p className="mb-3 text-xs text-slate-500">Use https:// URLs or site paths such as /images/properties/apartment-1.svg.</p>
          <div className="space-y-2">
            {state.images.map((image, index) => (
              <div key={index} className="grid items-center gap-2 sm:grid-cols-[1fr_10rem_auto_auto]">
                <Input aria-label={`Image ${index + 1} URL`} value={image.image_url} onChange={(e) => updateImage(index, { image_url: e.target.value })} placeholder="https://…" />
                <Input aria-label={`Image ${index + 1} caption`} value={image.caption} onChange={(e) => updateImage(index, { caption: e.target.value })} placeholder="Caption" />
                <Checkbox label="Primary" checked={image.is_primary} onChange={() => updateImage(index, { is_primary: true })} />
                <Button variant="ghost" size="sm" aria-label={`Remove image ${index + 1}`} onClick={() => set('images', state.images.filter((_, i) => i !== index))} icon={<Trash2 className="h-4 w-4" />} />
              </div>
            ))}
          </div>
          {errors.images && <p className="mt-1 text-xs text-rose-600">{errors.images}</p>}
          <Button variant="secondary" size="sm" className="mt-3" icon={<Plus className="h-4 w-4" />} onClick={() => set('images', [...state.images, { image_url: '', caption: '', is_primary: false }])}>
            Add image
          </Button>
        </fieldset>
      </form>
    </Modal>
  )
}
