import './ClubCard.css'

export default function ClubCard({ club }) {
  const handleAddToCalendar = (e) => {
    e.preventDefault()
    // Placeholder: would open Google Calendar add flow
    alert(`Adding "${club.name}" to your calendar — coming soon!`)
  }

  return (
    <article className="club-card">
      <div className="club-card__header">
        <div className="club-card__icon" aria-hidden>
          ⚔
        </div>
        <div className="club-card__meta">
          <span className="club-card__day">{club.meetingDay}</span>
          <span className="club-card__time">{club.meetingTime}</span>
        </div>
      </div>
      <h2 className="club-card__name">{club.name}</h2>
      <p className="club-card__description">{club.description}</p>
      <div className="club-card__tags">
        {club.tags.map((tag) => (
          <span key={tag} className="club-card__tag">
            {tag}
          </span>
        ))}
      </div>
      <p className="club-card__location">
        <span className="club-card__location-dot" aria-hidden>📍</span>
        {club.location}
      </p>
      <div className="club-card__footer">
        <span className="club-card__members">{club.members} members</span>
        <button
          type="button"
          className="club-card__cta"
          onClick={handleAddToCalendar}
        >
          Add to Calendar
        </button>
      </div>
    </article>
  )
}
