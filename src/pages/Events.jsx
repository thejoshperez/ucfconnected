import { useState } from 'react'
import EventCard from '../components/EventCard'
import { useFilteredEvents } from '../features/events/hooks'
import './Events.css'

const FILTERS = [
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'today', label: 'Today' },
  { key: 'all', label: 'All' },
]

export default function Events() {
  const [filter, setFilter] = useState('upcoming')
  const [search, setSearch] = useState('')
  const { events, loading, error, reload } = useFilteredEvents(filter)

  const filteredEvents = search
    ? events.filter(
        (event) =>
          event.title?.toLowerCase().includes(search.toLowerCase()) ||
          event.club?.toLowerCase().includes(search.toLowerCase()) ||
          event.location?.toLowerCase().includes(search.toLowerCase()) ||
          event.description?.toLowerCase().includes(search.toLowerCase()),
      )
    : events

  return (
    <section className="events-page">
      <div className="events-page__hero">
        <div className="events-page__hero-bg" aria-hidden />
        <div className="events-page__hero-inner">
          <p className="events-page__badge">UCF Campus Events</p>
          <h1 className="events-page__title">
            Campus events,
            <br />
            <span className="events-page__title-accent">all in one place.</span>
          </h1>
          <p className="events-page__subtitle">
            Club meetings and events from UCF Instagram accounts, extracted by AI.
          </p>

          <div className="events-page__search-wrap">
            <span className="events-page__search-icon" aria-hidden>⌕</span>
            <input
              type="search"
              className="events-page__search"
              placeholder="Search events, clubs, or locations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search events"
            />
          </div>
        </div>
      </div>

      <div className="events-page__body">
        <div className="events-page__inner">
          <div className="events-page__head">
            <h2 className="events-page__section-title">
              {loading ? 'Events' : `${filteredEvents.length} event${filteredEvents.length !== 1 ? 's' : ''}`}
            </h2>

            <div className="events-page__filters" role="tablist" aria-label="Filter events">
              {FILTERS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  role="tab"
                  aria-selected={filter === item.key}
                  className={`events-page__filter${filter === item.key ? ' events-page__filter--active' : ''}`}
                  onClick={() => {
                    setFilter(item.key)
                    setSearch('')
                  }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {loading && (
            <div className="events-grid" aria-busy="true">
              {Array.from({ length: 6 }, (_, index) => (
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
              <button type="button" className="events-page__retry" onClick={reload}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && filteredEvents.length === 0 && (
            <p className="events-page__empty">
              {search
                ? 'No events match your search.'
                : filter === 'today'
                  ? 'No events found for today. Check back later!'
                  : 'No events found yet. Check back soon.'}
            </p>
          )}

          {!loading && !error && filteredEvents.length > 0 && (
            <div className="events-grid">
              {filteredEvents.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
