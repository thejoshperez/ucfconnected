import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import EventCard from '../components/EventCard'
import '../pages/Events.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function MyFeed() {
  const { token, username } = useAuth()
  const [follows, setFollows] = useState(null)
  const [allEvents, setAllEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadFeed = useCallback(async () => {
    if (!token) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const [followsRes, eventsRes] = await Promise.all([
        fetch(`${API_BASE}/auth/follows`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_BASE}/events?limit=200`)
      ])

      if (!followsRes.ok || !eventsRes.ok) {
        throw new Error('Could not load your feed')
      }

      const [followsData, eventsData] = await Promise.all([
        followsRes.json(),
        eventsRes.json()
      ])

      setFollows(followsData)
      setAllEvents(eventsData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadFeed()
  }, [loadFeed])

  const followSet = new Set(follows ? follows.map(f => f.toLowerCase()) : [])
  const feedEvents = allEvents.filter(e => e.club && followSet.has(e.club.toLowerCase()))

  const retryButtonStyle = {
    marginTop: '1rem', 
    padding: '0.5rem 1.5rem', 
    background: 'var(--ucf-black)', 
    color: 'var(--ucf-gold)', 
    border: 'none', 
    borderRadius: 'var(--radius-full)', 
    cursor: 'pointer', 
    fontFamily: 'inherit', 
    fontSize: '0.9rem', 
    fontWeight: 600,
    display: 'inline-block',
    textDecoration: 'none'
  }

  // State 1 — Unauthenticated
  if (!token) {
    return (
      <div className="events-page">
        <div className="events-page__hero">
          <div className="events-page__hero-bg" aria-hidden />
          <div className="events-page__hero-inner">
            <p className="events-page__badge">Personalized</p>
            <h1 className="events-page__title">
              Your Feed
            </h1>
            <p className="events-page__subtitle">
              Sign in with the button in the top right to see events from clubs you follow.
            </p>
            <Link to="/events" className="events-page__retry" style={retryButtonStyle}>Browse all events →</Link>
          </div>
        </div>
      </div>
    )
  }

  // State 2 — Loading
  if (loading) {
    return (
      <div className="events-page">
        <div className="events-page__state" style={{ marginTop: '6rem' }}>
          <div className="events-page__spinner" aria-label="Loading your feed" />
          <p>Loading your feed…</p>
        </div>
      </div>
    )
  }

  // State 3 — Error
  if (error !== null) {
    return (
      <div className="events-page">
        <div className="events-page__state events-page__state--error" style={{ marginTop: '6rem' }}>
          <p>Could not load your feed.</p>
          <p className="events-page__error-detail">{error}</p>
          <button type="button" className="events-page__retry" style={retryButtonStyle} onClick={loadFeed}>Retry</button>
        </div>
      </div>
    )
  }

  const heroSection = (
    <div className="events-page__hero">
      <div className="events-page__hero-bg" aria-hidden />
      <div className="events-page__hero-inner">
        <p className="events-page__badge">Personalized</p>
        <h1 className="events-page__title">
          My Feed
        </h1>
        <p className="events-page__subtitle">
          Events from clubs you follow, @{username}.
        </p>
      </div>
    </div>
  )

  // State 4 — Zero follows
  if (follows !== null && follows.length === 0) {
    return (
      <div className="events-page">
        {heroSection}
        <div className="events-page__body">
          <div className="events-page__inner">
            <p className="events-page__empty">
              You're not following any clubs yet.{' '}
              <Link to="/" style={{ color: 'var(--ucf-gold-dim)', fontWeight: 600 }}>
                Browse clubs to follow some →
              </Link>
            </p>
          </div>
        </div>
      </div>
    )
  }

  // State 5 + 6 — Populated feed / Empty feed
  return (
    <div className="events-page">
      {heroSection}
      <div className="events-page__body">
        <div className="events-page__inner">
          <div className="events-page__head">
            <h2 className="events-page__section-title">
              {feedEvents.length} event{feedEvents.length !== 1 ? 's' : ''} from {follows.length} followed club{follows.length !== 1 ? 's' : ''}
            </h2>
          </div>
          {feedEvents.length === 0
            ? <p className="events-page__empty">No events found from your followed clubs. Check back after the next scrape.</p>
            : <div className="events-grid">{feedEvents.map(e => <EventCard key={e.id} event={e} />)}</div>
          }
        </div>
      </div>
    </div>
  )
}
