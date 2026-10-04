import { api, setAccessToken } from './api'
import type { AuthResponse, Paginated, HistoryEntry, SavedPreferences, Preferences, User } from '../types/api'

export const userService = {
  async updateProfile(payload: Partial<Pick<User, 'first_name' | 'last_name' | 'phone'>>): Promise<User> {
    const { data } = await api.patch<User>('/users/me/', payload)
    return data
  },

  async changePassword(current_password: string, new_password: string): Promise<User> {
    const { data } = await api.post<AuthResponse>('/users/me/password/', { current_password, new_password })
    setAccessToken(data.access)
    return data.user
  },

  async getPreferences(): Promise<SavedPreferences> {
    const { data } = await api.get<SavedPreferences>('/preferences/')
    return data
  },

  async savePreferences(preferences: Preferences): Promise<SavedPreferences> {
    const { data } = await api.put<SavedPreferences>('/preferences/', preferences)
    return data
  },

  async getHistory(page = 1, pageSize = 10): Promise<Paginated<HistoryEntry>> {
    const { data } = await api.get<Paginated<HistoryEntry>>('/recommendations/history/', {
      params: { page, page_size: pageSize },
    })
    return data
  },

  async clearHistory(): Promise<void> {
    await api.delete('/recommendations/history/')
  },
}
