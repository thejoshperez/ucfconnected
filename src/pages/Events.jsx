import { useState, useEffect, useCallback } from 'react'
import EventCard from '../components/EventCard'
import './Events.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const FILTERS = [
  { key: 'upcoming', label: 'Upcoming', endpoint: '/events/upcoming' },
  { key: 'today',    label: 'Today',    endpoint: '/events/today'    },
  { key: 'all',      label: 'All',      endpoint: '/events'          },
]

export default function Events() {
  const [filter, setFilter]   = useState('upcoming')
  const [events, setEvents]   = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [search, setSearch]   = useState('')

  const activeEndpoint = FILTERS.find((f) => f.key === filter)?.endpoint ?? '/events/upcoming'

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}${activeEndpoint}`)
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const data = await res.json()
      setEvents(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [activeEndpoint])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  const filtered = search
    ? events.filter(
        (e) =>
          e.title?.toLowerCase().includes(search.toLowerCase()) ||
          e.club?.toLowerCase().includes(search.toLowerCase()) ||
          e.location?.toLowerCase().includes(search.toLowerCase()) ||
          e.description?.toLowerCase().includes(search.toLowerCase()),
      )
    : events

  return (
    <section className="events-page">
      {/* ── Page header ── */}
      <div className="events-page__hero">
        <div className="events-page__hero-bg" aria-hidden />
        <div className="events-page__hero-inner">
          <p className="events-page__badge">UCF Campus Events</p>
          <h1 className="events-page__title">
            Campus events,<br />
            <span className="events-page__title-accent">all in one place.</span>
          </h1>
          <p className="events-page__subtitle">
            Club meetings and events from UCF Instagram accounts, extracted by AI.
          </p>

          {/* Search */}
          <div className="events-page__search-wrap">
            <span className="events-page__search-icon" aria-hidden>⌕</span>
            <input
              type="search"
              className="events-page__search"
              placeholder="Search events, clubs, or locations…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search events"
            />
          </div>
        </div>
      </div>

      {/* ── Filter tabs + grid ── */}
      <div className="events-page__body">
        <div className="events-page__inner">
          <div className="events-page__head">
            <h2 className="events-page__section-title">
              {loading ? 'Events' : `${filtered.length} event${filtered.length !== 1 ? 's' : ''}`}
            </h2>

            <div className="events-page__filters" role="tablist" aria-label="Filter events">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  type="button"
                  role="tab"
                  aria-selected={filter === f.key}
                  className={`events-page__filter${filter === f.key ? ' events-page__filter--active' : ''}`}
                  onClick={() => { setFilter(f.key); setSearch('') }}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* States */}
          {loading && (
            <div className="events-grid" aria-busy="true">
              {Array.from({ length: 6 }, (_, i) => (
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
              <button type="button" className="events-page__retry" onClick={fetchEvents}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && filtered.length === 0 && (
            <p className="events-page__empty">
              {search
                ? 'No events match your search.'
                : filter === 'today'
                  ? 'No events found for today. Check back later!'
                  : 'No events found yet. Check back soon.'}
            </p>
          )}

          {!loading && !error && filtered.length > 0 && (
            <div className="events-grid">
              {filtered.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
