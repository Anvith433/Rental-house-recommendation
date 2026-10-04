import type { Criterion, Preferences } from '../../types/api'
import { CRITERION_LABELS, formatRupees, PRIORITY_LABELS } from '../../utils/format'
import { Badge } from '../ui/Badge'

function budgetText(preferences: Preferences): string {
  const { min_rent: min, max_rent: max } = preferences
  if (min != null && max != null) return `${formatRupees(min)} – ${formatRupees(max)}`
  if (max != null) return `Up to ${formatRupees(max)}`
  if (min != null) return `From ${formatRupees(min)}`
  return 'Any budget'
}

function triText(value: boolean | null | undefined, yes: string, no: string) {
  return value === true ? yes : value === false ? no : 'No preference'
}

export function PreferenceSummary({ preferences }: { preferences: Preferences }) {
  const rows: [string, string][] = [
    ['Location', preferences.location || 'Anywhere'],
    ['Budget', budgetText(preferences)],
    [
      'Bedrooms',
      preferences.bedrooms
        ? `${preferences.bedroom_mode === 'minimum' ? 'At least' : 'Exactly'} ${preferences.bedrooms}`
        : 'Any',
    ],
    ['Furnishing', triText(preferences.furnished, 'Furnished', 'Unfurnished')],
    ['Parking', preferences.required_parking ? 'Required' : triText(preferences.parking, 'Preferred', 'Not needed')],
  ]
  const priorities = Object.entries(preferences.priority ?? {}) as [Criterion, keyof typeof PRIORITY_LABELS][]
  return (
    <div className="space-y-4">
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs text-slate-500">{label}</dt>
            <dd className="font-medium text-slate-800">{value}</dd>
          </div>
        ))}
      </dl>
      {priorities.some(([, level]) => level === 'must_have') && (
        <div className="flex flex-wrap gap-1.5">
          {priorities
            .filter(([, level]) => level === 'must_have')
            .map(([criterion]) => (
              <Badge key={criterion} tone="brand">
                Must have: {CRITERION_LABELS[criterion]}
              </Badge>
            ))}
        </div>
      )}
    </div>
  )
}
