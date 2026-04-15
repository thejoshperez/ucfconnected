import { useState } from 'react'
import './EventCard.css'

function confidenceClass(confidence) {
  if (confidence >= 0.85) return 'event-card__confidence--high'
  if (confidence < 0.65) return 'event-card__confidence--low'
  return ''
}

function confidenceLabel(confidence) {
  return `${Math.round(confidence * 100)}% match`
}

/**
 * Best-effort parser for the messy event.date / event.time strings the LLM produces.
 * Returns { start: Date, end: Date } or null if a usable date cannot be recovered.
 */
function parseEventDateTime(dateStr, timeStr) {
  if (!dateStr) return null

  // Try 1: ISO 8601 string in dateStr (Gemini preferred format)
  const isoAttempt = new Date(dateStr)
  if (!isNaN(isoAttempt.getTime())) {
    const start = isoAttempt
    const end = new Date(start.getTime() + 60 * 60 * 1000) // +1 hour default
    return { start, end, allDay: false }
  }

  // Try 2: "March 21" / "March 21, 2025" style — append current year if missing
  const currentYear = new Date().getFullYear()
  const dateWithYear = /\d{4}/.test(dateStr) ? dateStr : `${dateStr} ${currentYear}`
  const combined = timeStr ? `${dateWithYear} ${timeStr}` : dateWithYear
  const loose = new Date(combined)
  if (!isNaN(loose.getTime())) {
    const start = loose
    const end = new Date(start.getTime() + 60 * 60 * 1000)
    return { start, end, allDay: !timeStr }
  }

  return null
}

/**
 * Format a Date into Google Calendar's YYYYMMDDTHHMMSSZ format (UTC).
 * For all-day events, Google expects YYYYMMDD with no time portion.
 */
function formatForGoogleCal(date, allDay) {
  if (allDay) {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}${m}${d}`
  }
  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

/**
 * Build a Google Calendar "add event" URL from an event object.
 * Falls back to leaving `dates` blank when the date cannot be parsed,
 * letting the user fill it in on the Google Calendar page.
 */
function generateGoogleCalendarUrl(event) {
  const base = 'https://calendar.google.com/calendar/render?action=TEMPLATE'
  const params = new URLSearchParams()
  params.set('text', event.title || 'Untitled Event')

  const detailsParts = []
  if (event.description) detailsParts.push(event.description)
  if (event.club) detailsParts.push(`Hosted by @${event.club}`)
  if (event.source_post_permalink) detailsParts.push(`Source: ${event.source_post_permalink}`)
  if (detailsParts.length) params.set('details', detailsParts.join('\n\n'))

  if (event.location) params.set('location', event.location)

  const parsed = parseEventDateTime(event.date, event.time)
  if (parsed) {
    const startStr = formatForGoogleCal(parsed.start, parsed.allDay)
    const endStr = formatForGoogleCal(parsed.end, parsed.allDay)
    params.set('dates', `${startStr}/${endStr}`)
  }
  // If parsing failed, `dates` is omitted — Google Calendar shows an empty date picker
  // for the user to fill in manually.

  return `${base}&${params.toString()}`
}

export default function EventCard({ event }) {
  const {
    id,
    title,
    club,
    date,
    time,
    location,
    description,
    confidence,
    source_post_permalink,
  } = event

  const [copied, setCopied] = useState(false)

  const eventUrl = `${window.location.origin}/events/${id}`

  async function handleShare() {
    // Tier 1: Native share sheet (mobile / PWA / modern desktop browsers)
    if (navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: 'Check out this event on KnightLife!',
          url: eventUrl,
        })
        return // success — stop here
      } catch (err) {
        // AbortError = user dismissed the sheet — not an actual failure
        if (err.name === 'AbortError') return
        console.error('[Share] navigator.share failed:', err)
        // fall through to clipboard tier
      }
    }

    // Tier 2: Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(eventUrl)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
        return // success — stop here
      } catch (err) {
        console.error('[Share] navigator.clipboard.writeText failed:', err)
        // fall through to prompt tier
      }
    } else {
      console.warn('[Share] navigator.clipboard unavailable (insecure context or unsupported browser)')
    }

    // Tier 3: window.prompt fallback — always fires if the first two tiers fail
    try {
      window.prompt('Copy this link:', eventUrl)
    } catch (err) {
      console.error('[Share] window.prompt failed — nothing more we can do:', err)
    }
  }

  return (
    <article className="event-card">
      {/* ── Header ── */}
      <div className="event-card__header">
        <div className="event-card__icon" aria-hidden>
          📅
        </div>
        {(date || time) && (
          <div className="event-card__datetime">
            {date && <span className="event-card__date">{date}</span>}
            {time && <span className="event-card__time">{time}</span>}
          </div>
        )}
      </div>

      {/* ── Club badge ── */}
      {club && (
        <span className="event-card__club">
          <span className="event-card__club-at">@</span>
          {club}
        </span>
      )}

      {/* ── Title ── */}
      <h2 className="event-card__title">{title}</h2>

      {/* ── Description ── */}
      {description && (
        <p className="event-card__description">{description}</p>
      )}

      {/* ── Location ── */}
      {location && (
        <p className="event-card__location">
          <span aria-hidden>📍</span>
          {location}
        </p>
      )}

      {/* ── Footer ── */}
      <div className="event-card__footer">
        <span className={`event-card__confidence ${confidenceClass(confidence)}`}>
          <span className="event-card__confidence-dot" aria-hidden />
          {confidenceLabel(confidence)}
        </span>
        <div className="event-card__actions">
          <a
            href={generateGoogleCalendarUrl(event)}
            target="_blank"
            rel="noopener noreferrer"
            className="event-card__calendar"
            aria-label="Add this event to Google Calendar"
          >
            Add to Cal
          </a>
          <button
            className="event-card__share"
            onClick={handleShare}
            aria-label="Share this event"
          >
            {copied ? 'Copied!' : 'Share ↗'}
          </button>
          {source_post_permalink && (
            <a
              href={source_post_permalink}
              target="_blank"
              rel="noopener noreferrer"
              className="event-card__source"
            >
              View post ↗
            </a>
          )}
        </div>
      </div>
    </article>
  )
}
