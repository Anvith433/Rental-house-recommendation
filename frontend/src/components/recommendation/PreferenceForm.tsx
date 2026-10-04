import { BedDouble, Car, IndianRupee, MapPin, SlidersHorizontal, Sofa } from 'lucide-react'
import { useId, useState, type FormEvent, type ReactNode } from 'react'
import type { BedroomMode, Criterion, PriorityConfig, PriorityLevel, Preferences } from '../../types/api'
import { CRITERIA, PRIORITY_LEVELS, SCORING_WEIGHTS } from '../../utils/constants'
import { CRITERION_LABELS, PRIORITY_LABELS } from '../../utils/format'
import { Button } from '../ui/Button'
import { Checkbox, Input, Select } from '../ui/Field'

type TriState = 'any' | 'yes' | 'no'

interface FormState {
  location: string
  minRent: string
  maxRent: string
  bedrooms: string
  bedroomMode: BedroomMode
  furnished: TriState
  parking: TriState
  requiredParking: boolean
  priority: Record<Criterion, PriorityLevel>
}

const DEFAULT_PRIORITY: Record<Criterion, PriorityLevel> = {
  location: 'important',
  budget: 'important',
  bedrooms: 'important',
  furnished: 'preferred',
  parking: 'optional',
}

function toTriState(value: boolean | null | undefined): TriState {
  return value === true ? 'yes' : value === false ? 'no' : 'any'
}

function fromTriState(value: TriState): boolean | null {
  return value === 'yes' ? true : value === 'no' ? false : null
}

function initialState(initial?: Preferences): FormState {
  return {
    location: initial?.location ?? '',
    minRent: initial?.min_rent != null ? String(initial.min_rent) : '',
    maxRent: initial?.max_rent != null ? String(initial.max_rent) : '',
    bedrooms: initial?.bedrooms != null ? String(initial.bedrooms) : '',
    bedroomMode: initial?.bedroom_mode ?? 'exact',
    furnished: toTriState(initial?.furnished),
    parking: toTriState(initial?.parking),
    requiredParking: initial?.required_parking ?? false,
    priority: { ...DEFAULT_PRIORITY, ...(initial?.priority ?? {}) } as Record<Criterion, PriorityLevel>,
  }
}

/** Convert the form into the API's preference shape, omitting unset values. */
function toPreferences(state: FormState): Preferences {
  const preferences: Preferences = {
    bedroom_mode: state.bedroomMode,
    required_parking: state.requiredParking,
    priority: state.priority as PriorityConfig,
  }
  if (state.location.trim()) preferences.location = state.location.trim()
  if (state.minRent) preferences.min_rent = Number(state.minRent)
  if (state.maxRent) preferences.max_rent = Number(state.maxRent)
  if (state.bedrooms) preferences.bedrooms = Number(state.bedrooms)
  const furnished = fromTriState(state.furnished)
  if (furnished !== null) preferences.furnished = furnished
  const parking = fromTriState(state.parking)
  if (parking !== null) preferences.parking = parking
  return preferences
}

function validate(state: FormState): Record<string, string> {
  const errors: Record<string, string> = {}
  const min = state.minRent ? Number(state.minRent) : null
  const max = state.maxRent ? Number(state.maxRent) : null
  if (min !== null && (Number.isNaN(min) || min < 0)) errors.min_rent = 'Enter a valid amount.'
  if (max !== null && (Number.isNaN(max) || max < 0)) errors.max_rent = 'Enter a valid amount.'
  if (min !== null && max !== null && min > max) errors.rent = 'Minimum budget cannot exceed maximum budget.'
  if (state.bedrooms && (!Number.isInteger(Number(state.bedrooms)) || Number(state.bedrooms) < 1))
    errors.bedrooms = 'Choose at least 1 bedroom.'
  return errors
}

function Segmented({
  label,
  value,
  onChange,
  options,
  icon,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
  icon?: ReactNode
}) {
  const id = useId()
  return (
    <fieldset>
      <legend id={id} className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-slate-700">
        {icon}
        {label}
      </legend>
      <div role="radiogroup" aria-labelledby={id} className="grid auto-cols-fr grid-flow-col rounded-lg bg-slate-100 p-1">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={value === option.value}
            onClick={() => onChange(option.value)}
            className={`rounded-md px-2 py-1.5 text-sm font-medium transition ${
              value === option.value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </fieldset>
  )
}

interface PreferenceFormProps {
  initial?: Preferences
  onSubmit: (preferences: Preferences) => void
  submitLabel: string
  loading?: boolean
  serverErrors?: Record<string, string>
  locations?: string[]
  footer?: ReactNode
}

export function PreferenceForm({
  initial,
  onSubmit,
  submitLabel,
  loading,
  serverErrors = {},
  locations = [],
  footer,
}: PreferenceFormProps) {
  const [state, setState] = useState<FormState>(() => initialState(initial))
  const [errors, setErrors] = useState<Record<string, string>>({})
  const listId = useId()
  const allErrors = { ...serverErrors, ...errors }

  const update = <K extends keyof FormState>(key: K, value: FormState[K]) => setState((s) => ({ ...s, [key]: value }))

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const found = validate(state)
    setErrors(found)
    if (Object.keys(found).length === 0) onSubmit(toPreferences(state))
  }

  const triOptions = [
    { value: 'any', label: 'Any' },
    { value: 'yes', label: 'Yes' },
    { value: 'no', label: 'No' },
  ]

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-6">
      <div>
        <Input
          label="Where do you want to live?"
          placeholder="e.g. HSR Layout"
          value={state.location}
          onChange={(e) => update('location', e.target.value)}
          leading={<MapPin className="h-4 w-4" />}
          list={listId}
          maxLength={100}
          error={allErrors.location}
        />
        <datalist id={listId}>
          {locations.map((location) => (
            <option key={location} value={location} />
          ))}
        </datalist>
      </div>

      <div>
        <p className="mb-1.5 flex items-center gap-1.5 text-sm font-medium text-slate-700">
          <IndianRupee className="h-4 w-4 text-slate-400" aria-hidden />
          Monthly budget
        </p>
        <div className="grid grid-cols-[1fr_auto_1fr] items-start gap-2">
          <Input
            aria-label="Minimum rent"
            type="number"
            inputMode="numeric"
            min={0}
            step={500}
            placeholder="Min ₹"
            value={state.minRent}
            onChange={(e) => update('minRent', e.target.value)}
            error={allErrors.min_rent}
          />
          <span className="pt-2.5 text-slate-400">—</span>
          <Input
            aria-label="Maximum rent"
            type="number"
            inputMode="numeric"
            min={0}
            step={500}
            placeholder="Max ₹"
            value={state.maxRent}
            onChange={(e) => update('maxRent', e.target.value)}
            error={allErrors.max_rent}
          />
        </div>
        {allErrors.rent && <p className="mt-1.5 text-xs text-rose-600">{allErrors.rent}</p>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Select
          label="Bedrooms"
          value={state.bedrooms}
          onChange={(e) => update('bedrooms', e.target.value)}
          error={allErrors.bedrooms}
        >
          <option value="">Any</option>
          {[1, 2, 3, 4, 5].map((count) => (
            <option key={count} value={count}>
              {count} {count === 1 ? 'bedroom' : 'bedrooms'}
            </option>
          ))}
        </Select>
        <Segmented
          label="Bedroom requirement"
          icon={<BedDouble className="h-4 w-4 text-slate-400" aria-hidden />}
          value={state.bedroomMode}
          onChange={(value) => update('bedroomMode', value as BedroomMode)}
          options={[
            { value: 'exact', label: 'Exact' },
            { value: 'minimum', label: 'At least' },
          ]}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Segmented
          label="Furnished"
          icon={<Sofa className="h-4 w-4 text-slate-400" aria-hidden />}
          value={state.furnished}
          onChange={(value) => update('furnished', value as TriState)}
          options={triOptions}
        />
        <Segmented
          label="Parking"
          icon={<Car className="h-4 w-4 text-slate-400" aria-hidden />}
          value={state.parking}
          onChange={(value) => update('parking', value as TriState)}
          options={triOptions}
        />
      </div>

      <Checkbox
        label="Parking is a hard requirement"
        description="Only show homes with parking, whatever else matches."
        checked={state.requiredParking}
        onChange={(e) => update('requiredParking', e.target.checked)}
      />

      <fieldset className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
        <legend className="flex items-center gap-1.5 px-1 text-sm font-semibold text-slate-800">
          <SlidersHorizontal className="h-4 w-4 text-slate-500" aria-hidden />
          How much does each preference matter?
        </legend>
        <p className="mb-3 text-xs text-slate-500">
          Must-have multiplies a criterion's points by 1.5 and costs 20 points if missed; optional halves them.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {CRITERIA.map((criterion) => (
            <Select
              key={criterion}
              label={`${CRITERION_LABELS[criterion]} · ${SCORING_WEIGHTS[criterion]} pts`}
              value={state.priority[criterion]}
              onChange={(e) =>
                update('priority', { ...state.priority, [criterion]: e.target.value as PriorityLevel })
              }
              error={allErrors.priority && criterion === 'location' ? allErrors.priority : undefined}
            >
              {PRIORITY_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {PRIORITY_LABELS[level]}
                </option>
              ))}
            </Select>
          ))}
        </div>
      </fieldset>

      {footer}

      <Button type="submit" size="lg" loading={loading} className="w-full">
        {submitLabel}
      </Button>
    </form>
  )
}
