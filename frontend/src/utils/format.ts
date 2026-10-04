import type { Criterion, PreferenceName, PriorityLevel, PropertyType } from '../types/api'

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const compact = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 })

export function formatRupees(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return inr.format(value)
}

export function formatRupeesShort(value: number): string {
  if (value >= 100000) return `₹${compact.format(value / 100000)}L`
  if (value >= 1000) return `₹${compact.format(value / 1000)}k`
  return `₹${value}`
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function availabilityLabel(value: string | null): string {
  if (!value) return 'Available now'
  const date = new Date(value)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date <= today ? 'Available now' : `Available from ${formatDate(value)}`
}

export const PROPERTY_TYPE_LABELS: Record<PropertyType, string> = {
  apartment: 'Apartment',
  independent_house: 'Independent house',
  villa: 'Villa',
  studio: 'Studio',
  penthouse: 'Penthouse',
}

export const PRIORITY_LABELS: Record<PriorityLevel, string> = {
  must_have: 'Must have',
  important: 'Important',
  preferred: 'Preferred',
  optional: 'Optional',
}

export const CRITERION_LABELS: Record<Criterion, string> = {
  location: 'Location',
  budget: 'Budget',
  bedrooms: 'Bedrooms',
  furnished: 'Furnishing',
  parking: 'Parking',
}

export const PREFERENCE_LABELS: Record<PreferenceName, string> = {
  ...CRITERION_LABELS,
  minimum_budget: 'Minimum budget',
}

export function amenityLabel(value: string): string {
  const special: Record<string, string> = {
    water_supply_24x7: '24×7 water supply',
    cctv: 'CCTV',
    wifi: 'Wi-Fi',
  }
  if (special[value]) return special[value]
  const text = value.replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function bhkLabel(bedrooms: number, type: PropertyType): string {
  return type === 'studio' ? 'Studio' : `${bedrooms} BHK`
}

export function scoreTone(score: number): 'excellent' | 'good' | 'fair' | 'low' {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'fair'
  return 'low'
}
