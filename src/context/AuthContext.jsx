import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import {
  fetchCurrentUser,
  fetchFollowedOrganizations,
  followOrganization,
  loginUser,
  registerUser,
  resendCurrentUserVerification,
  unfollowOrganization,
  updateCurrentUserSettings,
  verifyCurrentUserEmail,
} from '../features/auth/api'
import { ApiError } from '../lib/apiClient'

const TOKEN_KEY = 'kl_token'
const USER_KEY = 'kl_user'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [follows, setFollows] = useState([])
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem(USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })

  const persistToken = useCallback((nextToken) => {
    localStorage.setItem(TOKEN_KEY, nextToken)
    setToken(nextToken)
  }, [])

  const persistUser = useCallback((nextUser) => {
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
    setUser(nextUser)
  }, [])

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem('kl_username')
    setToken(null)
    setFollows([])
    setUser(null)
  }, [])

  const syncFollows = useCallback(async (authToken) => {
    if (!authToken) {
      setFollows([])
      return []
    }

    try {
      const data = await fetchFollowedOrganizations(authToken)
      const nextFollows = Array.isArray(data) ? data : []
      setFollows(nextFollows)
      return nextFollows
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearAuth()
      }
      throw error
    }
  }, [clearAuth])

  const fetchMe = useCallback(async (authToken) => {
    try {
      const data = await fetchCurrentUser(authToken)
      persistUser(data)
      return data
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearAuth()
      }
      return null
    }
  }, [clearAuth, persistUser])

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY)
    if (storedToken) {
      fetchMe(storedToken)
      syncFollows(storedToken).catch(() => {
        // Ignore passive hydration failures.
      })
    }
  }, [fetchMe, syncFollows])

  const register = useCallback(async (username, password, email) => {
    const data = await registerUser({ username, password, email })
    persistToken(data.access_token)
    await fetchMe(data.access_token)
    await syncFollows(data.access_token)
    return data
  }, [fetchMe, persistToken, syncFollows])

  const login = useCallback(async (username, password) => {
    const data = await loginUser({ username, password })
    persistToken(data.access_token)
    await fetchMe(data.access_token)
    await syncFollows(data.access_token)
    return data
  }, [fetchMe, persistToken, syncFollows])

  const logout = useCallback(() => {
    clearAuth()
  }, [clearAuth])

  const verifyEmail = useCallback(async (code) => {
    if (!token) throw new Error('Not authenticated')
    const data = await verifyCurrentUserEmail(token, code)
    persistUser(data)
    return data
  }, [persistUser, token])

  const resendVerification = useCallback(async () => {
    if (!token) throw new Error('Not authenticated')
    return resendCurrentUserVerification(token)
  }, [token])

  const followClub = useCallback(async (clubInstagram) => {
    if (!token) throw new Error('Not logged in')
    const result = await followOrganization(token, clubInstagram)
    setFollows((prev) => (
      prev.some((value) => value.toLowerCase() === clubInstagram.toLowerCase())
        ? prev
        : [...prev, clubInstagram]
    ))
    return result
  }, [token])

  const unfollowClub = useCallback(async (clubInstagram) => {
    if (!token) throw new Error('Not logged in')
    const result = await unfollowOrganization(token, clubInstagram)
    setFollows((prev) => (
      prev.filter((value) => value.toLowerCase() !== clubInstagram.toLowerCase())
    ))
    return result
  }, [token])

  const fetchFollows = useCallback(async () => {
    if (!token) throw new Error('Not authenticated')
    return syncFollows(token)
  }, [syncFollows, token])

  const isFollowingClub = useCallback((clubInstagram) => {
    if (!clubInstagram) return false
    return follows.some((value) => value.toLowerCase() === clubInstagram.toLowerCase())
  }, [follows])

  const updateUserSettings = useCallback(async (settings) => {
    const updatedUser = { ...user, ...settings }
    persistUser(updatedUser)

    if (!token) return
    try {
      await updateCurrentUserSettings(token, settings)
    } catch (err) {
      console.warn('[AuthContext] updateUserSettings sync failed:', err.message)
    }
  }, [persistUser, token, user])

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        username: user?.username ?? null,
        login,
        register,
        logout,
        followClub,
        unfollowClub,
        fetchFollows,
        follows,
        isFollowingClub,
        verifyEmail,
        resendVerification,
        updateUserSettings,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
