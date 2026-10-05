// Single typed API client. No `fetch` calls anywhere else in the app.
// Normalises FastAPI error envelopes: `{detail: string}` and
// `{detail: [{loc,msg,type}, ...]}` (422 validation errors) both become a
// single readable string. Never render [object Object].

import type {
  ActiveModel,
  Dataset,
  DatasetPreview,
  DataQuality,
  Diagnostic,
  DiagnosticRequest,
  DiagnosticSummary,
  LoginRequest,
  LoginResponse,
  MaintenanceItem,
  Measurement,
  Notification,
  Thresholds,
  TrainingRequest,
  TrainingRun,
  User,
  UserBatteryOverview,
  ValidationErrorItem,
  Vehicle,
  VehicleDetail,
} from '../types/api'

const TOKEN_KEY = 'evsoh_token'

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // storage unavailable (private mode) - fail silently, auth will not persist
  }
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Normalise a FastAPI error response body into a single human readable
 * string. Handles both the plain HTTPException shape and the 422
 * validation-error array shape. Exported for unit testing.
 */
export function normalizeErrorDetail(body: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (body === null || body === undefined) return fallback
  if (typeof body === 'string') return body

  const detail = (body as { detail?: unknown }).detail

  if (typeof detail === 'string' && detail.length > 0) return detail

  if (Array.isArray(detail)) {
    const messages = (detail as ValidationErrorItem[])
      .map((item) => {
        const loc = Array.isArray(item.loc)
          ? item.loc.filter((part) => part !== 'body').join('.')
          : ''
        return loc ? `${loc}: ${item.msg}` : item.msg
      })
      .filter(Boolean)
    if (messages.length > 0) return messages.join('; ')
  }

  return fallback
}

interface RequestOptions {
  method?: string
  body?: BodyInit | object | null
  query?: Record<string, string | number | boolean | undefined | null>
}

function buildQuery(query?: RequestOptions['query']): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, String(value))
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query } = options
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let finalBody: BodyInit | undefined
  if (body instanceof FormData) {
    finalBody = body
  } else if (body !== undefined && body !== null) {
    headers['Content-Type'] = 'application/json'
    finalBody = JSON.stringify(body)
  }

  let res: Response
  try {
    res = await fetch(`/api${path}${buildQuery(query)}`, {
      method,
      headers,
      body: finalBody,
    })
  } catch {
    throw new ApiError(
      'Unable to reach the server. Confirm the backend is running and try again.',
      0,
    )
  }

  if (res.status === 204) {
    return undefined as T
  }

  const contentType = res.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')
  const parsed = isJson
    ? await res.json().catch(() => null)
    : await res.text().catch(() => null)

  if (!res.ok) {
    throw new ApiError(normalizeErrorDetail(parsed, `Request failed (${res.status}).`), res.status)
  }

  return parsed as T
}

export const api = {
  auth: {
    login: (body: LoginRequest) => request<LoginResponse>('/auth/login', { method: 'POST', body }),
    me: () => request<User>('/auth/me'),
  },
  config: {
    thresholds: () => request<Thresholds>('/config/thresholds'),
  },
  datasets: {
    list: () => request<Dataset[]>('/datasets'),
    upload: (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return request<Dataset>('/datasets/upload', { method: 'POST', body: formData })
    },
    get: (id: number) => request<Dataset>(`/datasets/${id}`),
    preview: (id: number, limit = 20) =>
      request<DatasetPreview>(`/datasets/${id}/preview`, { query: { limit } }),
    quality: (id: number) => request<DataQuality>(`/datasets/${id}/quality`),
    remove: (id: number) => request<void>(`/datasets/${id}`, { method: 'DELETE' }),
  },
  training: {
    create: (body: TrainingRequest) => request<TrainingRun>('/training/runs', { method: 'POST', body }),
    list: () => request<TrainingRun[]>('/training/runs'),
    get: (id: number) => request<TrainingRun>(`/training/runs/${id}`),
  },
  models: {
    list: () => request<TrainingRun[]>('/models'),
    active: () => request<ActiveModel | null>('/models/active'),
    deploy: (runId: number) => request<ActiveModel>(`/models/${runId}/deploy`, { method: 'POST' }),
  },
  vehicles: {
    list: (q?: string) => request<Vehicle[]>('/vehicles', { query: { q } }),
    get: (vehicleCode: string) => request<VehicleDetail>(`/vehicles/${encodeURIComponent(vehicleCode)}`),
  },
  batteries: {
    lookup: (code: string) => request<VehicleDetail>('/batteries/lookup', { query: { code } }),
    measurements: (serial: string) =>
      request<Measurement[]>(`/batteries/${encodeURIComponent(serial)}/measurements`),
  },
  diagnostics: {
    create: (body: DiagnosticRequest) => request<Diagnostic>('/diagnostics', { method: 'POST', body }),
    list: (params?: { code?: string; limit?: number }) =>
      request<Diagnostic[]>('/diagnostics', { query: params }),
    summary: () => request<DiagnosticSummary>('/diagnostics/summary'),
  },
  me: {
    battery: () => request<UserBatteryOverview>('/me/battery'),
    batteryHistory: () => request<Measurement[]>('/me/battery/history'),
    maintenance: () => request<MaintenanceItem[]>('/me/maintenance'),
  },
  notifications: {
    list: () => request<Notification[]>('/notifications'),
    markRead: (id: number) => request<Notification>(`/notifications/${id}/read`, { method: 'POST' }),
    markAllRead: () => request<void>('/notifications/read-all', { method: 'POST' }),
  },
}
