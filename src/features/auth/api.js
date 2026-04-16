import { apiRequest } from '../../lib/apiClient'

export function registerUser({ username, password, email }) {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: { username, password, email },
  })
}

export function loginUser({ username, password }) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: { username, password },
  })
}

export function fetchCurrentUser(token) {
  return apiRequest('/auth/me', { token })
}

export function verifyCurrentUserEmail(token, code) {
  return apiRequest('/auth/verify-email', {
    method: 'POST',
    token,
    body: { code },
  })
}

export function resendCurrentUserVerification(token) {
  return apiRequest('/auth/resend-verification', {
    method: 'POST',
    token,
  })
}

export function followOrganization(token, clubInstagram) {
  return apiRequest(`/auth/follow/${encodeURIComponent(clubInstagram)}`, {
    method: 'POST',
    token,
  })
}

export function unfollowOrganization(token, clubInstagram) {
  return apiRequest(`/auth/follow/${encodeURIComponent(clubInstagram)}`, {
    method: 'DELETE',
    token,
  })
}

export function fetchFollowedOrganizations(token) {
  return apiRequest('/auth/follows', { token })
}

export function updateCurrentUserSettings(token, settings) {
  return apiRequest('/auth/me', {
    method: 'PATCH',
    token,
    body: settings,
  })
}
