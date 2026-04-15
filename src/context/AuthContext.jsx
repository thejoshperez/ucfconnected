import { createContext, useContext, useState, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const TOKEN_KEY = 'kl_token'
const USERNAME_KEY = 'kl_username'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [username, setUsername] = useState(() => localStorage.getItem(USERNAME_KEY))

  const _persistAuth = useCallback((accessToken, user) => {
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USERNAME_KEY, user)
    setToken(accessToken)
    setUsername(user)
  }, [])

  const register = useCallback(async (user, password) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Registration failed')
    _persistAuth(data.access_token, data.username)
    return data
  }, [_persistAuth])

  const login = useCallback(async (user, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Login failed')
    _persistAuth(data.access_token, data.username)
    return data
  }, [_persistAuth])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USERNAME_KEY)
    setToken(null)
    setUsername(null)
  }, [])

  const followClub = useCallback(async (clubInstagram) => {
    if (!token) throw new Error('Not logged in')
    const res = await fetch(`${API_BASE}/auth/follow/${clubInstagram}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Follow failed')
    return data // { status: "followed" | "already_following", ... }
  }, [token])

  return (
    <AuthContext.Provider value={{ token, username, login, register, logout, followClub }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
