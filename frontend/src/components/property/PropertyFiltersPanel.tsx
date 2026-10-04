import { RotateCcw } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import type { PropertyFilters, PropertyType } from '../../types/api'
import { PROPERTY_TYPES } from '../../utils/constants'
import { PROPERTY_TYPE_LABELS } from '../../utils/format'
import { Button } from '../ui/Button'
import { Input, Select } from '../ui/Field'

interface Props {
  filters: PropertyFilters
  locations: string[]
  onApply: (filters: PropertyFilters) => void
  onReset: () => void
}

type Draft = Record<'location' | 'min_rent' | 'max_rent' | 'bedrooms' | 'bathrooms' | 'furnished' | 'parking' | 'property_type', string>

function toDraft(filters: PropertyFilters): Draft {
  const asString = (value: unknown) => (value === undefined || value === null ? '' : String(value))
  return {
    location: asString(filters.location),
    min_rent: asString(filters.min_rent),
    max_rent: asString(filters.max_rent),
    bedrooms: asString(filters.bedrooms),
    bathrooms: asString(filters.bathrooms),
    furnished: asString(filters.furnished),
    parking: asString(filters.parking),
    property_type: asString(filters.property_type),
  }
}

export function PropertyFiltersPanel({ filters, locations, onApply, onReset }: Props) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(filters))
  const [error, setError] = useState('')

  const set = (key: keyof Draft) => (event: { target: { value: string } }) =>
    setDraft((current) => ({ ...current, [key]: event.target.value }))

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const min = draft.min_rent ? Number(draft.min_rent) : undefined
    const max = draft.max_rent ? Number(draft.max_rent) : undefined
    if ((min !== undefined && min < 0) || (max !== undefined && max < 0)) {
      setError('Rent cannot be negative.')
      return
    }
    if (min !== undefined && max !== undefined && min > max) {
      setError('Minimum rent cannot exceed maximum rent.')
      return
    }
    setError('')
    onApply({
      location: draft.location.trim() || undefined,
      min_rent: min,
      max_rent: max,
      bedrooms: draft.bedrooms ? Number(draft.bedrooms) : undefined,
      bathrooms: draft.bathrooms ? Number(draft.bathrooms) : undefined,
      furnished: draft.furnished ? draft.furnished === 'true' : undefined,
      parking: draft.parking ? draft.parking === 'true' : undefined,
      property_type: (draft.property_type || undefined) as PropertyType | undefined,
    })
  }

  return (
    <form onSubmit={submit} className="space-y-4" aria-label="Filter properties">
      <Select label="Location" value={draft.location} onChange={set('location')}>
        <option value="">All localities</option>
        {locations.map((location) => (
          <option key={location} value={location}>
            {location}
          </option>
        ))}
      </Select>
      <div className="grid grid-cols-2 gap-3">
        <Input label="Min rent" type="number" min={0} step={1000} inputMode="numeric" placeholder="₹" value={draft.min_rent} onChange={set('min_rent')} />
        <Input label="Max rent" type="number" min={0} step={1000} inputMode="numeric" placeholder="₹" value={draft.max_rent} onChange={set('max_rent')} />
      </div>
      {error && <p className="text-xs text-rose-600">{error}</p>}
      <div className="grid grid-cols-2 gap-3">
        <Select label="Bedrooms" value={draft.bedrooms} onChange={set('bedrooms')}>
          <option value="">Any</option>
          {[1, 2, 3, 4].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </Select>
        <Select label="Bathrooms" value={draft.bathrooms} onChange={set('bathrooms')}>
          <option value="">Any</option>
          {[1, 2, 3].map((n) => (
            <option key={n} value={n}>
              {n}+
            </option>
          ))}
        </Select>
      </div>
      <Select label="Property type" value={draft.property_type} onChange={set('property_type')}>
        <option value="">All types</option>
        {PROPERTY_TYPES.map((type) => (
          <option key={type} value={type}>
            {PROPERTY_TYPE_LABELS[type]}
          </option>
        ))}
      </Select>
      <div className="grid grid-cols-2 gap-3">
        <Select label="Furnished" value={draft.furnished} onChange={set('furnished')}>
          <option value="">Any</option>
          <option value="true">Furnished</option>
          <option value="false">Unfurnished</option>
        </Select>
        <Select label="Parking" value={draft.parking} onChange={set('parking')}>
          <option value="">Any</option>
          <option value="true">With parking</option>
          <option value="false">No parking</option>
        </Select>
      </div>
      <div className="flex gap-2 pt-2">
        <Button type="submit" className="flex-1">
          Apply filters
        </Button>
        <Button variant="ghost" onClick={onReset} icon={<RotateCcw className="h-4 w-4" />} aria-label="Reset filters" />
      </div>
    </form>
  )
}
