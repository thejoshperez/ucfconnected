import { useCallback, useEffect, useState } from 'react'
import {
  fetchAllEvents,
  fetchClubEvents,
  fetchEventDetail,
  fetchEventsForFilter,
  rsvpToEvent,
} from './api'
import { fetchFollowedOrganizations } from '../auth/api'
import { getErrorMessage } from '../../lib/apiClient'

function normalizeEventKeyPart(value) {
  return typeof value === 'string'
    ? value.replace(/\s+/g, ' ').trim().toLowerCase()
    : ''
}

function getEventSignature(event) {
  const club = normalizeEventKeyPart(event?.club)
  const title = normalizeEventKeyPart(event?.title)

  if (!club || !title) return null

  const structuredStart = normalizeEventKeyPart(event?.start_at)
  const rawSchedule = normalizeEventKeyPart(`${event?.date || ''} ${event?.time || ''}`)
  const when = structuredStart || rawSchedule
  const location = normalizeEventKeyPart(event?.location)

  // Only collapse duplicates when there is enough scheduling/location context
  // to avoid merging unrelated events that merely share a title.
  if (!when && !location) return null

  return `${club}::${title}::${when}::${location}`
}

function dedupeEvents(events) {
  const seen = new Set()

  return events.filter((event) => {
    const signature = getEventSignature(event)
    if (!signature) return true
    if (seen.has(signature)) return false
    seen.add(signature)
    return true
  })
}

export function useFilteredEvents(filterKey, token = null) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchEventsForFilter(filterKey, token)
      setEvents(Array.isArray(data) ? dedupeEvents(data) : [])
    } catch (error) {
      setError(getErrorMessage(error, 'Could not load events.'))
    } finally {
      setLoading(false)
    }
  }, [filterKey, token])

  useEffect(() => {
    reload()
  }, [reload])

  return { events, loading, error, reload }
}

export function useClubEventsData(instagram, token = null) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotFound(false)

    try {
      const data = await fetchClubEvents(instagram, token)
      setEvents(Array.isArray(data) ? dedupeEvents(data) : [])
    } catch (error) {
      if (error?.status === 404) {
        setNotFound(true)
        setEvents([])
      } else {
        setError(getErrorMessage(error, 'Could not load club events.'))
      }
    } finally {
      setLoading(false)
    }
  }, [instagram, token])

  useEffect(() => {
    reload()
  }, [reload])

  return { events, loading, error, notFound, reload }
}

export function useEventDetailData(eventId, token = null) {
  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotFound(false)

    try {
      const data = await fetchEventDetail(eventId, token)
      setEvent(data)
    } catch (error) {
      if (error?.status === 404) {
        setNotFound(true)
        setEvent(null)
      } else {
        setError(getErrorMessage(error, 'Could not load event.'))
      }
    } finally {
      setLoading(false)
    }
  }, [eventId, token])

  useEffect(() => {
    reload()
  }, [reload])

  return { event, loading, error, notFound, reload }
}

export function useRsvpAction(eventId, token) {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const submit = useCallback(async () => {
    if (!token) return null

    setSubmitting(true)
    setError(null)
    try {
      return await rsvpToEvent(eventId, token)
    } catch (error) {
      const message = getErrorMessage(error, 'Could not RSVP.')
      setError(message)
      throw error
    } finally {
      setSubmitting(false)
    }
  }, [eventId, token])

  return { submit, submitting, error, setError }
}

export function useSquadActivityEvents(token) {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const reload = useCallback(async () => {
    if (!token) {
      setEvents([])
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await fetchAllEvents(200, token)
      const deduped = Array.isArray(data) ? dedupeEvents(data) : []
      setEvents(
        deduped.filter((event) => event.current_user_going || event.squad_members_going?.length > 0)
      )
    } catch (error) {
      setError(getErrorMessage(error, 'Could not load squad activity.'))
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    reload()
  }, [reload])

  return { events, loading, error, reload }
}

export function useFollowedEventsFeed(token) {
  const [follows, setFollows] = useState(null)
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const reload = useCallback(async () => {
    if (!token) {
      setLoading(false)
      setFollows(null)
      setEvents([])
      return
    }

    setLoading(true)
    setError(null)
    try {
      const [followsData, eventsData] = await Promise.all([
        fetchFollowedOrganizations(token),
        fetchAllEvents(200, token),
      ])

      setFollows(Array.isArray(followsData) ? followsData : [])
      setEvents(Array.isArray(eventsData) ? dedupeEvents(eventsData) : [])
    } catch (error) {
      setError(getErrorMessage(error, 'Could not load your feed.'))
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    reload()
  }, [reload])

  return { follows, events, loading, error, reload }
}
