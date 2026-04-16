import { apiRequest } from '../../lib/apiClient'

const EVENT_FILTER_ENDPOINTS = {
  upcoming: '/events/upcoming',
  today: '/events/today',
  all: '/events',
}

export function fetchEventsForFilter(filterKey, token = null) {
  const endpoint = EVENT_FILTER_ENDPOINTS[filterKey] || EVENT_FILTER_ENDPOINTS.upcoming
  return apiRequest(endpoint, { token })
}

export function fetchClubEvents(instagram, token = null) {
  return apiRequest(`/events/club/${encodeURIComponent(instagram)}`, { token })
}

export function fetchEventDetail(eventId, token = null) {
  return apiRequest(`/events/${eventId}`, { token })
}

export function rsvpToEvent(eventId, token) {
  return apiRequest(`/events/${eventId}/attendance`, {
    method: 'POST',
    token,
  })
}

export function fetchAllEvents(limit = 200, token = null) {
  return apiRequest(`/events?limit=${limit}`, { token })
}

export function injectAdminEvent(payload, adminKey) {
  return apiRequest('/events/admin/inject', {
    method: 'POST',
    body: payload,
    headers: {
      'x-admin-key': adminKey,
    },
  })
}
