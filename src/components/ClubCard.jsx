import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './ClubCard.css'

const TRUNCATE_AT = 120

export default function ClubCard({ club }) {
  const { followClub, unfollowClub, username, user, isFollowingClub } = useAuth()
  const [followLoading, setFollowLoading] = useState(false)
  const [followError, setFollowError] = useState(false)
  const isFollowing = isFollowingClub(club.instagram)

  const handleFollow = async (e) => {
    e.preventDefault()
    e.stopPropagation()

    if (!username) {
      alert('Sign in first to follow clubs!')
      return
    }

    if (!user?.email_verified) {
      alert('Please verify your email to follow clubs. Check the banner at the top of the page.')
      return
    }

    setFollowLoading(true)
    setFollowError(false)
    try {
      if (isFollowing) {
        await unfollowClub(club.instagram)
      } else {
        await followClub(club.instagram)
      }
    } catch (err) {
      console.error('[Follow] error:', err)
      setFollowError(true)
    } finally {
      setFollowLoading(false)
    }
  }

  const needsTruncation = club.description.length > TRUNCATE_AT
  const visibleDescription = needsTruncation
    ? `${club.description.substring(0, TRUNCATE_AT).trimEnd()}...`
    : club.description

  return (
    <article className="club-card">
      <h2 className="club-card__name">{club.name}</h2>

      <p className="club-card__description">{visibleDescription}</p>

      <div className="club-card__tags">
        {club.tags.map((tag) => (
          <span key={tag} className="club-card__tag">
            {tag}
          </span>
        ))}
      </div>

      <div className="club-card__footer">
        {club.instagram && (
          <Link
            to={`/events/club/${club.instagram}`}
            className="club-card__events-link"
          >
            Learn More &rarr;
          </Link>
        )}
        
        <button
          type="button"
          className={`club-detail__follow${isFollowing ? ' club-detail__follow--done' : ''}`}
          onClick={handleFollow}
          aria-pressed={isFollowing}
          title={isFollowing ? 'Click to unfollow this club' : 'Follow this club'}
          disabled={followLoading}
        >
          {followLoading
            ? '...'
            : followError
              ? 'Error - retry'
              : isFollowing
                ? 'Following ✓'
                : 'Follow'}
        </button>
      </div>
    </article>
  )
}
