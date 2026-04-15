import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import NotFound from './NotFound'
import './Events.css'
import './EventDetail.css'
import '../components/EventCard.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function confidenceClass(confidence) {
  if (confidence >= 0.85) return 'event-card__confidence--high'
  if (confidence < 0.65) return 'event-card__confidence--low'
  return ''
}

function confidenceLabel(confidence) {
  return `${Math.round(confidence * 100)}% match`
}

function parseEventDateTime(dateStr, timeStr) {
  if (!dateStr) return null

  const isoAttempt = new Date(dateStr)
  if (!isNaN(isoAttempt.getTime())) {
    const start = isoAttempt
    const end = new Date(start.getTime() + 60 * 60 * 1000)
    return { start, end, allDay: false }
  }

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

function formatForGoogleCal(date, allDay) {
  if (allDay) {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}${m}${d}`
  }
  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

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

  return `${base}&${params.toString()}`
}

export default function EventDetail() {
  const { id } = useParams()
  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    async function fetchEvent() {
      try {
        const res = await fetch(`${API_BASE}/events/${id}`)
        if (!res.ok) {
          throw new Error('Event not found')
        }
        const data = await res.json()
        setEvent(data)
        document.title = data.title ? `${data.title} | KnightLife` : 'KnightLife'
        
        if (data.title) {
          let ogTitle = document.querySelector('meta[property="og:title"]')
          if (!ogTitle) {
            ogTitle = document.createElement('meta')
            ogTitle.setAttribute('property', 'og:title')
            document.head.appendChild(ogTitle)
          }
          ogTitle.setAttribute('content', data.title)
        }
        
        if (data.description) {
          let ogDesc = document.querySelector('meta[property="og:description"]')
          if (!ogDesc) {
            ogDesc = document.createElement('meta')
            ogDesc.setAttribute('property', 'og:description')
            document.head.appendChild(ogDesc)
          }
          ogDesc.setAttribute('content', data.description)
        }

      } catch (err) {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    fetchEvent()
    
    return () => {
      document.title = 'KnightLife'
      const ogTitle = document.querySelector('meta[property="og:title"]')
      if (ogTitle) ogTitle.setAttribute('content', '')
      const ogDesc = document.querySelector('meta[property="og:description"]')
      if (ogDesc) ogDesc.setAttribute('content', '')
    }
  }, [id])

  async function handleShare() {
    if (!event) return
    const eventUrl = `${window.location.origin}/events/${event.id}`

    if (navigator.share) {
      try {
        await navigator.share({
          title: event.title,
          text: 'Check out this event on KnightLife!',
          url: eventUrl,
        })
        return
      } catch (err) {
        if (err.name === 'AbortError') return
        console.error('[Share] navigator.share failed:', err)
      }
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(eventUrl)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
        return
      } catch (err) {
        console.error('[Share] navigator.clipboard.writeText failed:', err)
      }
    } else {
      console.warn('[Share] navigator.clipboard unavailable (insecure context or unsupported browser)')
    }

    try {
      window.prompt('Copy this link:', eventUrl)
    } catch (err) {
      console.error('[Share] window.prompt failed — nothing more we can do:', err)
    }
  }

  if (loading) {
    return (
      <div className="events-page__state" style={{ marginTop: '4rem' }}>
        <div className="events-page__spinner" aria-label="Loading event"></div>
        <p>Loading event…</p>
      </div>
    )
  }

  if (error || !event) {
    return <NotFound />
  }

  const { title, club, date, time, location, description, confidence, source_post_permalink } = event

  return (
    <div className="event-detail">
      <Link to="/events" className="event-detail__back">← Back to Events</Link>

      <div className="event-detail__hero">
        {(date || time) && (
          <div className="event-detail__date-badge">
            {date && <span>{date}</span>}
            {time && <span>{time}</span>}
          </div>
        )}
        <span className={`event-card__confidence ${confidenceClass(confidence)}`}>
          <span className="event-card__confidence-dot" />
          {confidenceLabel(confidence)}
        </span>
      </div>

      <h1 className="event-detail__title">{title}</h1>

      {club && (
        <span className="event-card__club">
          <span className="event-card__club-at">@</span>{club}
        </span>
      )}

      {location && (
        <p className="event-detail__location">
          <span aria-hidden>📍</span>{location}
        </p>
      )}

      {description && (
        <p className="event-detail__description">{description}</p>
      )}

      <hr className="event-detail__divider" />

      <div className="event-detail__actions">
        <a href={generateGoogleCalendarUrl(event)} target="_blank" rel="noopener noreferrer"
           className="event-card__calendar">Add to Cal</a>
        <button className="event-card__share" onClick={handleShare}>
          {copied ? 'Copied!' : 'Share ↗'}
        </button>
        {source_post_permalink && (
          <a href={source_post_permalink} target="_blank" rel="noopener noreferrer"
             className="event-card__source">View post ↗</a>
        )}
      </div>
    </div>
  )
}
