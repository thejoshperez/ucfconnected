import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import EventCard from '../components/EventCard'
import { clubs } from '../data/clubs'
import './Events.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ClubEvents() {
  const { instagram } = useParams()
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [notFound, setNotFound] = useState(false)

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
    document.title = `${displayName} Events | KnightLife`
    fetchClubEvents()
    return () => { document.title = 'KnightLife' }
  }, [fetchClubEvents, displayName])

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
            {' / '}
            <Link to="/events" style={{ color: 'inherit', textDecoration: 'none' }}>
              Events
            </Link>
          </p>
          <h1 className="events-page__title">{displayName}</h1>
          {clubData?.description && (
            <p className="events-page__subtitle">{clubData.description}</p>
          )}
        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────────────────── */}
      <div className="events-page__body">
        <div className="events-page__inner">

          {loading && (
            <div className="events-page__state">
              <div className="events-page__spinner" aria-label="Loading events" />
              <p>Loading events…</p>
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
              No events have been detected for {displayName} yet — check back after
              the next scrape.{' '}
              <Link to="/events" style={{ color: 'var(--ucf-gold-dim)', fontWeight: 600 }}>
                Browse all events &rarr;
              </Link>
            </p>
          )}

          {!loading && !error && !notFound && events.length > 0 && (
            <>
              <div className="events-page__head">
                <h2 className="events-page__section-title">
                  {events.length} event{events.length !== 1 ? 's' : ''}
                </h2>
              </div>
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
