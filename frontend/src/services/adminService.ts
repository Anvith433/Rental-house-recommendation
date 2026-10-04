import { api } from './api'
import type { AdminProperty, AdminUser, Analytics, Inquiry, Paginated, PropertyFilters, Role } from '../types/api'

export const adminService = {
  async analytics(): Promise<Analytics> {
    const { data } = await api.get<Analytics>('/admin/analytics/')
    return data
  },

  async properties(filters: PropertyFilters = {}): Promise<Paginated<AdminProperty>> {
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== ''))
    const { data } = await api.get<Paginated<AdminProperty>>('/admin/properties/', { params })
    return data
  },

  async users(params: { page?: number; search?: string; role?: Role | '' } = {}): Promise<Paginated<AdminUser>> {
    const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ''))
    const { data } = await api.get<Paginated<AdminUser>>('/admin/users/', { params: clean })
    return data
  },

  async updateUser(id: number, payload: Partial<Pick<AdminUser, 'role' | 'is_active'>>): Promise<AdminUser> {
    const { data } = await api.patch<AdminUser>(`/admin/users/${id}/`, payload)
    return data
  },

  async inquiries(page = 1, status = ''): Promise<Paginated<Inquiry>> {
    const params: Record<string, string | number> = { page }
    if (status) params.status = status
    const { data } = await api.get<Paginated<Inquiry>>('/admin/inquiries/', { params })
    return data
  },

  async updateInquiry(id: number, status: Inquiry['status']): Promise<Inquiry> {
    const { data } = await api.patch<Inquiry>(`/admin/inquiries/${id}/`, { status })
    return data
  },
}
