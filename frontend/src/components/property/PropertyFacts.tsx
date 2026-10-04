import { Bath, BedDouble, Car, Maximize, Sofa } from 'lucide-react'
import type { PropertySummary } from '../../types/api'
import { bhkLabel } from '../../utils/format'

export function PropertyFacts({ property, compact = false }: { property: PropertySummary; compact?: boolean }) {
  const facts = [
    { icon: BedDouble, label: bhkLabel(property.bedrooms, property.property_type) },
    { icon: Bath, label: `${property.bathrooms} bath` },
    { icon: Maximize, label: `${property.area_sqft.toLocaleString('en-IN')} sq ft` },
  ]
  if (!compact) {
    facts.push(
      { icon: Sofa, label: property.furnished ? 'Furnished' : 'Unfurnished' },
      { icon: Car, label: property.parking ? 'Parking' : 'No parking' },
    )
  }
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-sm text-slate-600">
      {facts.map(({ icon: Icon, label }) => (
        <li key={label} className="flex items-center gap-1.5">
          <Icon className="h-4 w-4 text-slate-400" aria-hidden />
          {label}
        </li>
      ))}
    </ul>
  )
}
