import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import EventCard from '../components/EventCard'
import { useClubEventsData } from '../features/events/hooks'
import { clubs } from '../data/clubs'
import './Events.css'

export default function ClubEvents() {
  const { instagram } = useParams()
  const { followClub, unfollowClub, username, user, isFollowingClub } = useAuth()
  const { events, loading, error, notFound, reload } = useClubEventsData(instagram)
  const [followLoading, setFollowLoading] = useState(false)
  const [followError, setFollowError] = useState(false)

  const clubData = clubs.find((club) => club.instagram === instagram)
  const displayName = clubData?.name || `@${instagram}`
  const isFollowing = isFollowingClub(instagram)

  useEffect(() => {
    document.title = `${displayName} | KnightLife`
    return () => {
      document.title = 'KnightLife'
    }
  }, [displayName])

  const handleFollow = async (event) => {
    event.preventDefault()
    event.stopPropagation()

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
        await unfollowClub(instagram)
      } else {
        await followClub(instagram)
      }
    } catch (error) {
      console.error('[Follow] error:', error)
      setFollowError(true)
    } finally {
      setFollowLoading(false)
    }
  }

  return (
    <section className="events-page">
      <div className="events-page__hero">
        <div className="events-page__hero-bg" aria-hidden />
        <div className="events-page__hero-inner">
          <p className="events-page__badge">
            <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>
              &larr; Clubs
            </Link>
          </p>
          <h1 className="events-page__title">{displayName}</h1>
          {clubData?.description && (
            <p className="events-page__subtitle">{clubData.description}</p>
          )}

          {clubData?.tags?.length > 0 && (
            <div className="club-detail__tags">
              {clubData.tags.map((tag) => (
                <span key={tag} className="club-detail__tag">{tag}</span>
              ))}
            </div>
          )}

          <div className="club-detail__meta">
            {clubData?.members && (
              <span className="club-detail__meta-item">👥 {clubData.members} members</span>
            )}
          </div>

          <div className="club-detail__actions">
            {instagram && (
              <a
                href={`https://instagram.com/${instagram}`}
                target="_blank"
                rel="noopener noreferrer"
                className="club-detail__instagram"
              >
                @{instagram} ↗
              </a>
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
        </div>
      </div>

      <div className="events-page__body">
        <div className="events-page__inner">
          <div className="events-page__head">
            <h2 className="events-page__section-title">All Events</h2>
          </div>

          {loading && (
            <div className="events-grid" aria-busy="true">
              {Array.from({ length: 3 }, (_, index) => (
                <div key={index} className="event-card-skeleton" aria-hidden="true">
                  <div className="event-card-skeleton__header">
                    <div className="event-card-skeleton__shimmer event-card-skeleton__icon" />
                    <div className="event-card-skeleton__shimmer event-card-skeleton__date" />
                  </div>
                  <div className="event-card-skeleton__shimmer event-card-skeleton__badge" />
                  <div className="event-card-skeleton__shimmer event-card-skeleton__title" />
                  <div className="event-card-skeleton__shimmer event-card-skeleton__line" />
                  <div className="event-card-skeleton__shimmer event-card-skeleton__line event-card-skeleton__line--short" />
                  <div className="event-card-skeleton__footer">
                    <div className="event-card-skeleton__shimmer event-card-skeleton__pill" />
                    <div className="event-card-skeleton__actions">
                      <div className="event-card-skeleton__shimmer event-card-skeleton__btn" />
                      <div className="event-card-skeleton__shimmer event-card-skeleton__btn" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="events-page__state events-page__state--error">
              <p>Could not load events. Is the API running?</p>
              <p className="events-page__error-detail">{error}</p>
              <button
                type="button"
                className="events-page__retry"
                onClick={reload}
                style={{ marginTop: '1rem', padding: '0.5rem 1.5rem', background: 'var(--ucf-black)', color: 'var(--ucf-gold)', border: 'none', borderRadius: 'var(--radius-full)', cursor: 'pointer', fontWeight: 600 }}
              >
                Retry
              </button>
            </div>
          )}

          {!loading && !error && notFound && (
            <p className="events-page__empty">
              No upcoming events found for this club.{' '}
              <Link to="/events" style={{ color: 'var(--ucf-gold-dim)', fontWeight: 600 }}>
                Browse all events &rarr;
              </Link>
            </p>
          )}

          {!loading && !error && !notFound && events.length > 0 && (
            <div className="events-grid">
              {events.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
