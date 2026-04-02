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
    title,
    club,
    date,
    time,
    location,
    description,
    confidence,
    source_post_id,
  } = event

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
        {source_post_id && (
          <a
            href={`https://www.instagram.com/p/${source_post_id}/`}
            target="_blank"
            rel="noopener noreferrer"
            className="event-card__source"
          >
            View post ↗
          </a>
        )}
      </div>
    </article>
  )
}
