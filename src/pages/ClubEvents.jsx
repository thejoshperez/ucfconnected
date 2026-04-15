import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import EventCard from '../components/EventCard'
import { clubs } from '../data/clubs'
import './Events.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ClubEvents() {
  const { instagram } = useParams()
  const { followClub, username, token } = useAuth()
  
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)
  
  const [followStatus, setFollowStatus] = useState(null) // null | 'followed' | 'already_following' | 'error'
  const [followLoading, setFollowLoading] = useState(false)

  // Look up static club data for display name and description
  const clubData = clubs.find((c) => c.instagram === instagram)
  const displayName = clubData?.name || `@${instagram}`

  const fetchClubEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotFound(false)
    try {
      const res = await fetch(`${API_BASE}/events/club/${encodeURIComponent(instagram)}`)
      if (res.status === 404) {
        setNotFound(true)
        return
      }
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const data = await res.json()
      setEvents(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [instagram])

  useEffect(() => {
    document.title = `${displayName} | KnightLife`
    fetchClubEvents()
    return () => { document.title = 'KnightLife' }
  }, [fetchClubEvents, displayName])

  // Pre-fetch following status on mount if authenticated
  useEffect(() => {
    async function checkFollowStatus() {
      if (!token || !instagram) return
      try {
        const res = await fetch(`${API_BASE}/auth/follows`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
          const follows = await res.json()
          if (follows.some(f => f.toLowerCase() === instagram.toLowerCase())) {
            setFollowStatus('already_following')
          }
        }
      } catch (e) {
        // Ignore silent failure on mount checking
      }
    }
    checkFollowStatus()
  }, [token, instagram])

  const handleFollow = async (e) => {
    e.preventDefault()
    e.stopPropagation()

    if (!username) {
      alert('Sign in first to follow clubs!')
      return
    }

    setFollowLoading(true)
    try {
      const result = await followClub(instagram)
      setFollowStatus(result.status) // 'followed' | 'already_following'
    } catch (err) {
      console.error('[Follow] error:', err)
      setFollowStatus('error')
    } finally {
      setFollowLoading(false)
      setTimeout(() => setFollowStatus(null), 3000)
    }
  }

  return (
    <section className="events-page">

      {/* ── Hero ─────────────────────────────────────────────────────── */}
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
              {clubData.tags.map(tag => (
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
                @{instagram} &#x2197;
              </a>
            )}
            <button
              type="button"
              className={`club-detail__follow${followStatus === 'followed' ? ' club-detail__follow--done' : ''}`}
              onClick={handleFollow}
              disabled={followLoading || followStatus === 'followed' || followStatus === 'already_following'}
            >
              {followLoading ? '…'
                : followStatus === 'followed' ? 'Following ✓'
                : followStatus === 'already_following' ? 'Already following'
                : followStatus === 'error' ? 'Error — retry'
                : 'Follow'}
            </button>
          </div>

        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────── */}
      <div className="events-page__body">
        <div className="events-page__inner">
          <div className="events-page__head">
            <h2 className="events-page__section-title">All Events</h2>
          </div>

          {loading && (
            <div className="events-grid" aria-busy="true">
              {Array.from({ length: 3 }, (_, i) => (
                <div key={i} className="event-card-skeleton" aria-hidden="true">
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
              <p>Could not load events — is the API running?</p>
              <p className="events-page__error-detail">{error}</p>
              <button 
                type="button" 
                className="events-page__retry" 
                onClick={fetchClubEvents}
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
            <>
              <div className="events-grid">
                {events.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            </>
          )}

        </div>
      </div>
    </section>
  )
}
