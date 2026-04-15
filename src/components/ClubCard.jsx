import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './ClubCard.css'

const TRUNCATE_AT = 80

export default function ClubCard({ club }) {
  const [isExpanded, setIsExpanded] = useState(false)

  const { followClub, username } = useAuth()
  const [followStatus, setFollowStatus] = useState(null) // null | 'followed' | 'already_following' | 'error'
  const [followLoading, setFollowLoading] = useState(false)

  const handleFollow = async (e) => {
    e.preventDefault()
    e.stopPropagation()

    if (!username) {
      alert('Sign in first to follow clubs!')
      return
    }

    setFollowLoading(true)
    try {
      const result = await followClub(club.instagram)
      setFollowStatus(result.status) // 'followed' | 'already_following'
    } catch (err) {
      console.error('[Follow] error:', err)
      setFollowStatus('error')
    } finally {
      setFollowLoading(false)
      // Reset status display after 3 seconds
      setTimeout(() => setFollowStatus(null), 3000)
    }
  }

  const toggleExpanded = () => setIsExpanded((prev) => !prev)

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      toggleExpanded()
    }
  }

  const needsTruncation = club.description.length > TRUNCATE_AT
  const visibleDescription =
    !isExpanded && needsTruncation
      ? `${club.description.substring(0, TRUNCATE_AT).trimEnd()}…`
      : club.description

  return (
    <article
      className={`club-card${isExpanded ? ' club-card--expanded' : ''}`}
      onClick={toggleExpanded}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-expanded={isExpanded}
    >
      <div className="club-card__header">
        <div className="club-card__icon" aria-hidden>
          ⚔
        </div>
      </div>

      <h2 className="club-card__name">{club.name}</h2>

      <p className="club-card__description">{visibleDescription}</p>

      <div className="club-card__tags">
        {club.tags.map((tag) => (
          <span key={tag} className="club-card__tag">
            {tag}
          </span>
        ))}
      </div>

      {isExpanded && club.instagram && (
        <a
          href={`https://instagram.com/${club.instagram}`}
          target="_blank"
          rel="noopener noreferrer"
          className="club-card__instagram"
          onClick={(e) => e.stopPropagation()}
        >
          <span className="club-card__instagram-icon" aria-hidden>
            ⓘ
          </span>
          @{club.instagram}
        </a>
      )}

      {isExpanded && club.instagram && (
        <Link
          to={`/events/club/${club.instagram}`}
          className="club-card__events-link"
          onClick={(e) => e.stopPropagation()}
        >
          📅 See {club.name} events &rarr;
        </Link>
      )}

      <div className="club-card__footer">
        <span className="club-card__members">{club.members} members</span>
        <span className="club-card__toggle-hint" aria-hidden>
          {isExpanded ? 'Show less ▴' : 'Show more ▾'}
        </span>
        <button
          type="button"
          className={`club-card__cta${followStatus === 'followed' ? ' club-card__cta--done' : ''}`}
          onClick={handleFollow}
          disabled={followLoading || followStatus === 'followed' || followStatus === 'already_following'}
        >
          {followLoading
            ? '…'
            : followStatus === 'followed'
            ? 'Following ✓'
            : followStatus === 'already_following'
            ? 'Already following'
            : followStatus === 'error'
            ? 'Error — retry'
            : 'Follow'}
        </button>
      </div>
    </article>
  )
}
