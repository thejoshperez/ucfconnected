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
    // Mobile / PWA: use native share sheet
    if (navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: 'Check out this event on KnightLife!',
          url: eventUrl,
        })
      } catch (err) {
        // User cancelled the share sheet — not an error
        if (err.name !== 'AbortError') {
          console.error('Share failed:', err)
        }
      }
      return
    }

    // Desktop fallback: copy link to clipboard
    try {
      await navigator.clipboard.writeText(eventUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard API unavailable (e.g. insecure context)
      window.prompt('Copy this link:', eventUrl)
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
