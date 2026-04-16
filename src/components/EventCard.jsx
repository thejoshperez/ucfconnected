import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useRsvpAction } from '../features/events/hooks'
import './EventCard.css'
import {
  getEventDisplayDateTime,
  getGoogleCalendarUrl,
} from '../utils/eventActions'

export default function EventCard({ event }) {
  const { user, token } = useAuth()
  const {
    title,
    club,
    location,
    description,
    source_post_permalink,
    current_user_going,
    squad_members_going,
  } = event

  const [going, setGoing] = useState(Boolean(current_user_going))
  const { dateText, timeText } = getEventDisplayDateTime(event)
  const calendarUrl = getGoogleCalendarUrl(event)
  const {
    submit: submitRsvp,
    submitting: rsvpLoading,
  } = useRsvpAction(event.id, token)

  useEffect(() => {
    setGoing(Boolean(current_user_going))
  }, [current_user_going])

  async function handleRsvp() {
    if (!token) return
    try {
      await submitRsvp()
      setGoing(true)
    } catch {
      // Hook state already handles errors where needed.
    }
  }

  return (
    <article className="event-card">
      {(dateText || timeText) && (
        <div className="event-card__header">
          <div className="event-card__datetime">
            {dateText && <span className="event-card__date">{dateText}</span>}
            {timeText && <span className="event-card__time">{timeText}</span>}
          </div>
        </div>
      )}

      {club && (
        <span className="event-card__club">
          <span className="event-card__club-at">@</span>
          {club}
        </span>
      )}

      <h2 className="event-card__title">{title}</h2>

      {description && (
        <p className="event-card__description">{description}</p>
      )}

      {location && (
        <p className="event-card__location">
          <span className="event-card__location-label" aria-hidden>At</span>
          {location}
        </p>
      )}

      {going && (
        <div className="event-card__attendance event-card__attendance--self">
          You&apos;re going
        </div>
      )}

      {squad_members_going && squad_members_going.length > 0 && (
        <div className="event-card__attendance event-card__attendance--squad">
          {squad_members_going.length === 1
            ? `@${squad_members_going[0]} is going`
            : `${squad_members_going.length} squad members going`}
        </div>
      )}

      <div className="event-card__footer">
        <div className="event-card__actions">
          {user?.email_verified && (
            going ? (
              <button
                type="button"
                className="event-card__action event-card__action--secondary"
                disabled
              >
                Going
              </button>
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
              aria-label="Add this event to Google Calendar"
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
      </div>
    </article>
  )
}
