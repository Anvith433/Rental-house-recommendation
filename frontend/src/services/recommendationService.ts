import { api } from './api'
import type { RecommendationRequest, RecommendationResponse } from '../types/api'

export const recommendationService = {
  async recommend(request: RecommendationRequest): Promise<RecommendationResponse> {
    const { data } = await api.post<RecommendationResponse>('/recommendations/', request)
    return data
  },
}
