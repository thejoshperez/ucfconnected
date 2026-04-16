import { apiRequest } from '../../lib/apiClient'

export function fetchPublicSquads() {
  return apiRequest('/squads')
}

export function fetchMySquads(token) {
  return apiRequest('/squads/mine', { token })
}

export function createSquad(token, payload) {
  return apiRequest('/squads', {
    method: 'POST',
    token,
    body: payload,
  })
}

export function fetchSquadDetail(code) {
  return apiRequest(`/squads/${encodeURIComponent(code)}`)
}

export function joinSquad(code, token) {
  return apiRequest(`/squads/${encodeURIComponent(code)}/join`, {
    method: 'POST',
    token,
  })
}

export function approveSquadMember(code, userId, token) {
  return apiRequest(`/squads/${encodeURIComponent(code)}/members/${userId}/approve`, {
    method: 'POST',
    token,
  })
}

export function deleteSquad(code, token) {
  return apiRequest(`/squads/${encodeURIComponent(code)}`, {
    method: 'DELETE',
    token,
  })
}
