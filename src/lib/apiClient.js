const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function buildHeaders(body, token, headers) {
  const finalHeaders = new Headers(headers || {})

  if (body !== undefined && body !== null && !(body instanceof FormData) && !finalHeaders.has('Content-Type')) {
    finalHeaders.set('Content-Type', 'application/json')
  }

  if (token) {
    finalHeaders.set('Authorization', `Bearer ${token}`)
  }

  return finalHeaders
}

async function parseResponse(response) {
  if (response.status === 204) return null

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }

  const text = await response.text()
  return text ? { detail: text } : null
}

export async function apiRequest(path, options = {}) {
  const {
    method = 'GET',
    body,
    token,
    headers,
    signal,
  } = options

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: buildHeaders(body, token, headers),
    body:
      body === undefined || body === null || body instanceof FormData
        ? body
        : JSON.stringify(body),
    signal,
  })

  const data = await parseResponse(response)

  if (!response.ok) {
    const message =
      (data && typeof data === 'object' && 'detail' in data && data.detail) ||
      `Request failed with status ${response.status}`
    throw new ApiError(message, response.status, data)
  }

  return data
}

export function isNetworkError(error) {
  return error instanceof TypeError
}

export function getErrorMessage(error, fallbackMessage) {
  if (error instanceof ApiError) {
    return error.message || fallbackMessage
  }

  if (error instanceof Error) {
    return error.message || fallbackMessage
  }

  return fallbackMessage
}
