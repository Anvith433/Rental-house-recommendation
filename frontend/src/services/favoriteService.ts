import { api } from './api'
import type { Favorite, Paginated } from '../types/api'

export const favoriteService = {
  async list(page = 1, pageSize = 12): Promise<Paginated<Favorite>> {
    const { data } = await api.get<Paginated<Favorite>>('/favorites/', { params: { page, page_size: pageSize } })
    return data
  },

  async ids(): Promise<number[]> {
    const { data } = await api.get<{ ids: number[] }>('/favorites/ids/')
    return data.ids
  },

  async add(propertyId: number): Promise<void> {
    await api.post(`/favorites/${propertyId}/`)
  },

  async remove(propertyId: number): Promise<void> {
    await api.delete(`/favorites/${propertyId}/`)
  },
}
