import { isAxiosError } from 'axios'
import type { ApiErrorBody } from '../types/api'

export type ErrorKind = 'network' | 'unauthorized' | 'forbidden' | 'not_found' | 'validation' | 'rate_limited' | 'server'

export interface AppError {
  kind: ErrorKind
  message: string
  fieldErrors: Record<string, string>
}

function flattenDetail(value: unknown): string {
  if (Array.isArray(value)) return value.map(flattenDetail).join(' ')
  if (value && typeof value === 'object') return Object.values(value).map(flattenDetail).join(' ')
  return String(value)
}

/** Normalise any thrown value into a user-presentable error. */
export function toAppError(error: unknown): AppError {
  if (!isAxiosError<ApiErrorBody>(error)) {
    return { kind: 'server', message: 'Something went wrong. Please try again.', fieldErrors: {} }
  }
  if (!error.response) {
    return {
      kind: 'network',
      message: 'Unable to reach RentWise. Check your connection and try again.',
      fieldErrors: {},
    }
  }
  const { status, data } = error.response
  const body = data?.error
  const fieldErrors: Record<string, string> = {}
  if (body?.details && status === 400) {
    for (const [field, value] of Object.entries(body.details)) {
      fieldErrors[field] = flattenDetail(value)
    }
  }
  const kind: ErrorKind =
    status === 401
      ? 'unauthorized'
      : status === 403
        ? 'forbidden'
        : status === 404
          ? 'not_found'
          : status === 429
            ? 'rate_limited'
            : status >= 500
              ? 'server'
              : 'validation'
  const fallback: Record<ErrorKind, string> = {
    network: 'Network error.',
    unauthorized: 'Please sign in to continue.',
    forbidden: "You don't have permission to do that.",
    not_found: "We couldn't find what you were looking for.",
    validation: 'Please check the highlighted fields.',
    rate_limited: "You're doing that too often. Please wait a moment and try again.",
    server: 'Something went wrong on our side. Please try again shortly.',
  }
  const message = kind === 'server' || kind === 'rate_limited' ? fallback[kind] : body?.message || fallback[kind]
  return { kind, message, fieldErrors }
}
