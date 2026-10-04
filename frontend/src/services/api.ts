import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

/**
 * Centralised HTTP client.
 *
 * Token strategy: the short-lived access token lives only in this module's
 * memory (never localStorage), so injected scripts cannot read it from
 * storage. The refresh token is an HttpOnly cookie set by the API and is sent
 * automatically to /api/auth/*; JavaScript can never read it. After a reload
 * the session is restored by calling /auth/refresh/.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

let accessToken: string | null = null
let refreshPromise: Promise<string | null> | null = null
let sessionExpiredHandler: (() => void) | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export function hasAccessToken() {
  return accessToken !== null
}

export function onSessionExpired(handler: () => void) {
  sessionExpiredHandler = handler
}

/** Exchange the refresh cookie for a new access token. Concurrent callers share one request. */
export function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access: string }>(`${api.defaults.baseURL}/auth/refresh/`, null, { withCredentials: true })
      .then((response) => {
        setAccessToken(response.data.access)
        return response.data.access
      })
      .catch(() => {
        setAccessToken(null)
        return null
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean }

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined
    const isAuthEndpoint = config?.url?.startsWith('/auth/')
    if (error.response?.status === 401 && config && !config._retried && !isAuthEndpoint && accessToken) {
      config._retried = true
      const token = await refreshAccessToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
        return api(config)
      }
      sessionExpiredHandler?.()
    }
    return Promise.reject(error)
  },
)
