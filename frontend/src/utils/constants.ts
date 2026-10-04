import type { Criterion, PriorityLevel, PropertyType } from '../types/api'

export const AMENITIES = [
  'lift',
  'power_backup',
  'security',
  'gym',
  'swimming_pool',
  'clubhouse',
  'play_area',
  'wifi',
  'air_conditioning',
  'gated_community',
  'pet_friendly',
  'balcony',
  'modular_kitchen',
  'water_supply_24x7',
  'visitor_parking',
  'cctv',
] as const

export const PROPERTY_TYPES: PropertyType[] = ['apartment', 'independent_house', 'villa', 'studio', 'penthouse']
export const PRIORITY_LEVELS: PriorityLevel[] = ['must_have', 'important', 'preferred', 'optional']
export const CRITERIA: Criterion[] = ['location', 'budget', 'bedrooms', 'furnished', 'parking']

/** Mirrors rentals/recommendation_config.py – shown in the UI for transparency. */
export const SCORING_WEIGHTS: Record<Criterion, number> = {
  location: 30,
  budget: 25,
  bedrooms: 20,
  furnished: 15,
  parking: 10,
}

export const MAX_COMPARE = 4
export const PAGE_SIZE = 12
