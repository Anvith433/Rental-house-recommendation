export type Role = 'USER' | 'ADMIN'
export type PropertyType = 'apartment' | 'independent_house' | 'villa' | 'studio' | 'penthouse'
export type ListingStatus = 'active' | 'inactive' | 'flagged'
export type PriorityLevel = 'must_have' | 'important' | 'preferred' | 'optional'
export type BedroomMode = 'exact' | 'minimum'
export type Criterion = 'location' | 'budget' | 'bedrooms' | 'furnished' | 'parking'
export type PreferenceName = Criterion | 'minimum_budget'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone: string
  role: Role
  is_admin: boolean
  created_at: string
}

export interface AuthResponse {
  access: string
  user: User
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface PropertyImage {
  id?: number
  image_url: string
  caption: string
  is_primary: boolean
}

export interface PropertySummary {
  id: number
  title: string
  location: string
  city: string
  rent: number
  security_deposit: number
  bedrooms: number
  bathrooms: number
  area_sqft: number
  furnished: boolean
  parking: boolean
  property_type: PropertyType
  available_from: string | null
  status: ListingStatus
  primary_image: string | null
  created_at: string
}

export interface Property extends PropertySummary {
  description: string
  state: string
  latitude: string | null
  longitude: string | null
  floor: number | null
  total_floors: number | null
  amenities: string[]
  images: PropertyImage[]
  updated_at: string
}

export interface Explanation {
  summary: string
  strengths: string[]
  weaknesses: string[]
}

export interface MatchEvaluation {
  score: number
  matched_preferences: PreferenceName[]
  unmatched_preferences: PreferenceName[]
  score_breakdown: Partial<Record<Criterion, number>>
  explanation: Explanation
}

export interface PropertyDetail extends Property {
  match?: MatchEvaluation
}

export type PriorityConfig = Partial<Record<Criterion, PriorityLevel>>

export interface Preferences {
  location?: string
  min_rent?: number | null
  max_rent?: number | null
  bedrooms?: number | null
  bedroom_mode?: BedroomMode
  furnished?: boolean | null
  parking?: boolean | null
  required_parking?: boolean
  priority?: PriorityConfig
}

export interface SavedPreferences extends Preferences {
  updated_at: string | null
}

export interface RecommendationRequest extends Preferences {
  top_n?: number
  allow_budget_relaxation?: boolean
}

export interface Recommendation {
  rank: number
  property: PropertySummary
  score: number
  matched_preferences: PreferenceName[]
  unmatched_preferences: PreferenceName[]
  score_breakdown: Partial<Record<Criterion, number>>
  explanation: Explanation
}

export interface RecommendationResponse {
  recommendations: Recommendation[]
  total_matches: number
  requested_top_n: number
  returned_count: number
  filters_applied: RecommendationRequest
  budget_relaxed: boolean
  message?: string
  original_max_rent?: number
  relaxed_max_rent?: number
  relaxation_percentage?: number
}

export interface HistoryEntry {
  id: number
  request_preferences: RecommendationRequest
  result_property_ids: number[]
  results: Pick<PropertySummary, 'id' | 'title' | 'location' | 'rent' | 'bedrooms' | 'status'>[]
  top_score: number | null
  total_matches: number
  budget_relaxed: boolean
  latency_ms: number
  created_at: string
}

export interface Favorite {
  id: number
  property: PropertySummary
  created_at: string
}

export interface CompareResponse {
  properties: Property[]
  matches: Record<string, MatchEvaluation>
  has_saved_preferences: boolean
}

export interface LocationCount {
  location: string
  count: number
}

export interface Inquiry {
  id: number
  property: number
  property_title: string
  user_email: string
  user_name: string
  message: string
  phone: string
  status: 'new' | 'responded' | 'closed'
  created_at: string
}

export interface AdminUser {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone: string
  role: Role
  is_active: boolean
  last_login: string | null
  created_at: string
  favorites_count: number
  recommendations_count: number
}

export interface AdminProperty extends PropertySummary {
  updated_at: string
  favorites_count: number
  views_count: number
  inquiries_count: number
}

export interface EngineMetrics {
  since: string
  requests: number
  average_latency_ms: number | null
  average_candidates: number | null
  average_results: number | null
  budget_relaxation_rate: number | null
  empty_result_rate: number | null
}

export interface Analytics {
  users: { total: number; active: number; admins: number; new_last_7_days: number }
  properties: { total: number; active: number; inactive: number; flagged: number; average_rent: number | null }
  favorites: { total: number }
  inquiries: { total: number; new: number }
  interactions: { views_last_7_days: number }
  recommendations: {
    total: number
    last_7_days: number
    average_latency_ms: number | null
    average_candidates: number | null
    budget_relaxation_rate: number | null
  }
  recommendation_trend: { date: string; count: number }[]
  most_favorited: { id: number; title: string; location: string; favorites_total: number }[]
  most_viewed: { id: number; title: string; location: string; views_total: number }[]
  listings_by_location: { location: string; count: number }[]
  engine_metrics: EngineMetrics
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details: Record<string, unknown>
  }
}

export interface PropertyFilters {
  search?: string
  location?: string
  min_rent?: number
  max_rent?: number
  bedrooms?: number
  bathrooms?: number
  furnished?: boolean
  parking?: boolean
  property_type?: PropertyType
  ordering?: string
  page?: number
  page_size?: number
  status?: ListingStatus
}
