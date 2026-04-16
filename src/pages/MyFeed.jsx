import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useFollowedEventsFeed } from '../features/events/hooks'
import EventCard from '../components/EventCard'
import '../pages/Events.css'

export default function MyFeed() {
  const { token, username } = useAuth()
  const { follows, events: allEvents, loading, error, reload } = useFollowedEventsFeed(token)

  const followSet = new Set(follows ? follows.map((follow) => follow.toLowerCase()) : [])
  const followedClubEvents = allEvents.filter((event) => event.club && followSet.has(event.club.toLowerCase()))
  const followedEventIds = new Set(followedClubEvents.map((event) => event.id))
  const squadActivityEvents = allEvents.filter(
    (event) => event.squad_members_going?.length > 0 && !followedEventIds.has(event.id)
  )

  if (!token) {
    return (
      <div className="events-page">
        <div className="events-page__hero">
          <div className="events-page__hero-bg" aria-hidden />
          <div className="events-page__hero-inner">
            <p className="events-page__badge">Personalized</p>
            <h1 className="events-page__title">Your Feed</h1>
            <p className="events-page__subtitle">
              Sign in with the button in the top right to see events from clubs you follow.
            </p>
            <Link to="/events" className="events-page__retry">Browse all events →</Link>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="events-page">
        <div className="events-page__hero">
          <div className="events-page__hero-bg" aria-hidden />
          <div className="events-page__hero-inner">
            <p className="events-page__badge">Personalized</p>
            <h1 className="events-page__title">My Feed</h1>
            <p className="events-page__subtitle">
              Loading events for @{username}...
            </p>
          </div>
        </div>
        <div className="events-page__body">
          <div className="events-page__inner">
            <div className="events-page__state">
              <div className="events-page__spinner" aria-label="Loading your feed" />
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error !== null) {
    return (
      <div className="events-page">
        <div className="events-page__hero">
          <div className="events-page__hero-bg" aria-hidden />
          <div className="events-page__hero-inner">
            <p className="events-page__badge">Personalized</p>
            <h1 className="events-page__title">My Feed</h1>
          </div>
        </div>
        <div className="events-page__body">
          <div className="events-page__inner">
            <div className="events-page__state events-page__state--error">
              <p>Could not load your feed.</p>
              <p className="events-page__error-detail">{error}</p>
              <button type="button" className="events-page__retry" onClick={reload}>
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const heroSection = (
    <div className="events-page__hero">
      <div className="events-page__hero-bg" aria-hidden />
      <div className="events-page__hero-inner">
        <p className="events-page__badge">Personalized</p>
        <h1 className="events-page__title">My Feed</h1>
        <p className="events-page__subtitle">
          Events from clubs you follow and activity from your squad, @{username}.
        </p>
      </div>
    </div>
  )

  if (follows !== null && follows.length === 0) {
    return (
      <div className="events-page">
        {heroSection}
        <div className="events-page__body">
          <div className="events-page__inner">
            <p className="events-page__empty">
              You&apos;re not following any clubs yet.{' '}
              <Link to="/" style={{ color: 'var(--ucf-gold-dim)', fontWeight: 600 }}>
                Browse clubs to follow some →
              </Link>
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="events-page">
      {heroSection}
      <div className="events-page__body">
        <div className="events-page__inner">
          <div className="events-page__head">
            <h2 className="events-page__section-title">
              {followedClubEvents.length} event{followedClubEvents.length !== 1 ? 's' : ''} from {follows.length} followed club{follows.length !== 1 ? 's' : ''}
            </h2>
          </div>
          {followedClubEvents.length === 0 ? (
            <p className="events-page__empty">No events found from your followed clubs. Check back soon.</p>
          ) : (
            <div className="events-grid">
              {followedClubEvents.map((event) => <EventCard key={event.id} event={event} />)}
            </div>
          )}

          <div className="events-page__head" style={{ marginTop: '2rem' }}>
            <h2 className="events-page__section-title">Squad Activity</h2>
          </div>
          {squadActivityEvents.length === 0 ? (
            <p className="events-page__empty">No squad member RSVPs yet.</p>
          ) : (
            <div className="events-grid">
              {squadActivityEvents.map((event) => <EventCard key={event.id} event={event} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
