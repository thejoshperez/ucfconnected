import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  approveSquadMember,
  createSquad,
  deleteSquad,
  fetchMySquads,
  fetchPublicSquads,
  fetchSquadDetail,
  joinSquad,
} from './api'
import { getErrorMessage, isNetworkError } from '../../lib/apiClient'

export function useSquadsLandingData(token) {
  const [publicSquads, setPublicSquads] = useState([])
  const [mySquads, setMySquads] = useState([])
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    setLoading(true)

    try {
      const [publicData, myData] = await Promise.all([
        fetchPublicSquads(),
        token ? fetchMySquads(token) : Promise.resolve([]),
      ])

      setPublicSquads(Array.isArray(publicData) ? publicData : [])
      setMySquads(Array.isArray(myData) ? myData : [])
    } catch (error) {
      console.error('Failed to load squads landing data', error)
      setPublicSquads([])
      setMySquads([])
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    reload()
  }, [reload])

  return { publicSquads, mySquads, loading, reload }
}

export function useCreateSquad(token) {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const submit = useCallback(async ({ name, isPublic }) => {
    setSubmitting(true)
    setError(null)

    try {
      return await createSquad(token, { name, is_public: isPublic })
    } catch (error) {
      const message = isNetworkError(error)
        ? 'Could not reach the server - make sure the backend is running and try again.'
        : getErrorMessage(error, 'Failed to create squad.')
      setError(message)
      throw error
    } finally {
      setSubmitting(false)
    }
  }, [token])

  return { submit, submitting, error, setError }
}

export function useSquadDetail(code, currentUserId) {
  const displayCode = useMemo(() => code.toUpperCase(), [code])
  const [squad, setSquad] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  const reload = useCallback(async () => {
    setLoading(true)
    setNotFound(false)
    try {
      const data = await fetchSquadDetail(displayCode)
      setSquad(data)
      localStorage.setItem('last_squad_code', displayCode)
    } catch (error) {
      if (error?.status === 404) {
        setNotFound(true)
      } else {
        console.error(error)
      }
    } finally {
      setLoading(false)
    }
  }, [displayCode])

  useEffect(() => {
    reload()
  }, [reload])

  const myMemberEntry = useMemo(
    () => squad?.members?.find((member) => member.user_id === currentUserId),
    [currentUserId, squad]
  )

  return {
    squad,
    setSquad,
    loading,
    notFound,
    reload,
    displayCode,
    myMemberEntry,
  }
}

export function useSquadMembershipActions(code, token, setSquad) {
  const [joinLoading, setJoinLoading] = useState(false)
  const [joinError, setJoinError] = useState(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  const requestJoin = useCallback(async () => {
    setJoinLoading(true)
    setJoinError(null)
    try {
      const data = await joinSquad(code, token)
      setSquad(data)
      return data
    } catch (error) {
      setJoinError(getErrorMessage(error, 'Failed to join squad.'))
      throw error
    } finally {
      setJoinLoading(false)
    }
  }, [code, setSquad, token])

  const requestApprove = useCallback(async (userId) => {
    const data = await approveSquadMember(code, userId, token)
    setSquad(data)
    return data
  }, [code, setSquad, token])

  const requestDelete = useCallback(async () => {
    setDeleteLoading(true)
    try {
      await deleteSquad(code, token)
      localStorage.removeItem('last_squad_code')
    } finally {
      setDeleteLoading(false)
    }
  }, [code, token])

  return {
    requestJoin,
    joinLoading,
    joinError,
    setJoinError,
    requestApprove,
    requestDelete,
    deleteLoading,
  }
}
