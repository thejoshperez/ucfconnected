import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useEventDetailData, useRsvpAction } from '../features/events/hooks'
import NotFound from './NotFound'
import './Events.css'
import './EventDetail.css'
import '../components/EventCard.css'
import {
  getEventDisplayDateTime,
  getGoogleCalendarUrl,
} from '../utils/eventActions'

export default function EventDetail() {
  const { id } = useParams()
  const { user, token } = useAuth()
  const { event, loading, error, notFound } = useEventDetailData(id, token)
  const [going, setGoing] = useState(false)
  const {
    submit: submitRsvp,
    submitting: rsvpLoading,
    error: rsvpError,
  } = useRsvpAction(id, token)

  useEffect(() => {
    document.title = event?.title ? `${event.title} | KnightLife` : 'KnightLife'

    if (event?.title) {
      let ogTitle = document.querySelector('meta[property="og:title"]')
      if (!ogTitle) {
        ogTitle = document.createElement('meta')
        ogTitle.setAttribute('property', 'og:title')
        document.head.appendChild(ogTitle)
      }
      ogTitle.setAttribute('content', event.title)
    }

    if (event?.description) {
      let ogDesc = document.querySelector('meta[property="og:description"]')
      if (!ogDesc) {
        ogDesc = document.createElement('meta')
        ogDesc.setAttribute('property', 'og:description')
        document.head.appendChild(ogDesc)
      }
      ogDesc.setAttribute('content', event.description)
    }

    return () => {
      document.title = 'KnightLife'
      const ogTitle = document.querySelector('meta[property="og:title"]')
      if (ogTitle) ogTitle.setAttribute('content', '')
      const ogDesc = document.querySelector('meta[property="og:description"]')
      if (ogDesc) ogDesc.setAttribute('content', '')
    }
  }, [event])

  useEffect(() => {
    setGoing(Boolean(event?.current_user_going))
  }, [event?.current_user_going])

  async function handleRsvp() {
    if (!token) return
    try {
      await submitRsvp()
      setGoing(true)
    } catch {
      // Hook state already captures the error message.
    }
  }

  if (loading) {
    return (
      <div className="event-detail">
        <Link to="/events" className="event-detail__back">Back to Events</Link>
        <div className="event-detail__loading-state">
          <div className="events-page__spinner" aria-label="Loading event" />
        </div>
      </div>
    )
  }

  if (notFound) {
    return <NotFound />
  }

  if (error || !event) {
    return (
      <div className="event-detail">
        <Link to="/events" className="event-detail__back">Back to Events</Link>
        <p className="event-detail__error-msg">
          Could not load this event - the API may be unavailable.
        </p>
      </div>
    )
  }

  const { title, club, location, description, source_post_permalink } = event
  const { dateText, timeText } = getEventDisplayDateTime(event)
  const calendarUrl = getGoogleCalendarUrl(event)

  return (
    <div className="event-detail">
      <Link to="/events" className="event-detail__back">Back to Events</Link>

      <div className="event-detail__hero">
        {(dateText || timeText) && (
          <div className="event-detail__date-badge">
            {dateText && <span>{dateText}</span>}
            {timeText && <span>{timeText}</span>}
          </div>
        )}
      </div>

      <h1 className="event-detail__title">{title}</h1>

      {club && (
        <span className="event-card__club">
          <span className="event-card__club-at">@</span>{club}
        </span>
      )}

      {location && (
        <p className="event-detail__location">
          <span className="event-card__location-label" aria-hidden>At</span>{location}
        </p>
      )}

      {description && (
        <p className="event-detail__description">{description}</p>
      )}

      {going && (
        <p className="event-card__attendance event-card__attendance--self">
          You&apos;re going
        </p>
      )}

      {event.squad_members_going?.length > 0 && (
        <p className="event-card__attendance event-card__attendance--squad">
          {event.squad_members_going.length === 1
            ? `@${event.squad_members_going[0]} is going`
            : `${event.squad_members_going.length} squad members going`}
        </p>
      )}

      <hr className="event-detail__divider" />

      <div className="event-detail__actions">
        {user && (
          going ? (
            <button type="button" className="event-card__action event-card__action--secondary" disabled>Going</button>
          ) : (
            <button
              type="button"
              className="event-card__action event-card__action--secondary"
              onClick={handleRsvp}
              disabled={rsvpLoading}
            >
              {rsvpLoading ? '...' : "I'm Going"}
            </button>
          )
        )}
        {calendarUrl && (
          <a
            href={calendarUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="event-card__action event-card__action--primary"
          >
            Add to Calendar
          </a>
        )}
        {source_post_permalink && (
          <a
            href={source_post_permalink}
            target="_blank"
            rel="noopener noreferrer"
            className="event-card__action event-card__action--ghost"
          >
            View Post
          </a>
        )}
      </div>
      {rsvpError && (
        <p style={{ color: '#b91c1c', fontSize: '0.85rem', marginTop: '0.5rem' }}>
          {rsvpError}
        </p>
      )}
    </div>
  )
}
