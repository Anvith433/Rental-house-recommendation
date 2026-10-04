import { api } from './api'
import type {
  CompareResponse,
  LocationCount,
  Paginated,
  Property,
  PropertyDetail,
  PropertyFilters,
  PropertySummary,
} from '../types/api'

function cleanParams(filters: PropertyFilters): Record<string, string | number | boolean> {
  const params: Record<string, string | number | boolean> = {}
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== '') params[key] = value
  }
  return params
}

export type PropertyInput = Omit<Property, 'id' | 'created_at' | 'updated_at' | 'primary_image'>

export const propertyService = {
  async list(filters: PropertyFilters = {}): Promise<Paginated<PropertySummary>> {
    const { data } = await api.get<Paginated<PropertySummary>>('/properties/', { params: cleanParams(filters) })
    return data
  },

  async get(id: number | string): Promise<PropertyDetail> {
    const { data } = await api.get<PropertyDetail>(`/properties/${id}/`)
    return data
  },

  async compare(ids: number[]): Promise<CompareResponse> {
    const { data } = await api.get<CompareResponse>('/properties/compare/', { params: { ids: ids.join(',') } })
    return data
  },

  async locations(): Promise<LocationCount[]> {
    const { data } = await api.get<LocationCount[]>('/properties/locations/')
    return data
  },

  async inquire(id: number, message: string, phone: string): Promise<void> {
    await api.post(`/properties/${id}/inquiries/`, { message, phone })
  },

  async create(payload: Partial<PropertyInput>): Promise<Property> {
    const { data } = await api.post<Property>('/properties/', payload)
    return data
  },

  async update(id: number, payload: Partial<PropertyInput>): Promise<Property> {
    const { data } = await api.patch<Property>(`/properties/${id}/`, payload)
    return data
  },

  async remove(id: number): Promise<void> {
    await api.delete(`/properties/${id}/`)
  },
}
