import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import EventCard from '../components/EventCard'
import { useAuth } from '../context/AuthContext'
import { useSquadActivityEvents } from '../features/events/hooks'
import { getErrorMessage } from '../lib/apiClient'
import { useSquadDetail, useSquadMembershipActions } from '../features/squads/hooks'
import './Events.css'
import './Squads.css'

export default function SquadPage() {
  const { code } = useParams()
  const navigate = useNavigate()
  const { user, username, token } = useAuth()
  const [copied, setCopied] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const {
    squad,
    setSquad,
    loading,
    notFound,
    reload: fetchSquad,
    displayCode,
    myMemberEntry,
  } = useSquadDetail(code, user?.id)

  const {
    requestJoin,
    joinLoading,
    joinError,
    requestApprove,
    requestDelete,
    deleteLoading,
  } = useSquadMembershipActions(displayCode, token, setSquad)
  const {
    events: squadActivityEvents,
    loading: squadActivityLoading,
  } = useSquadActivityEvents(token)

  const isLoggedIn = Boolean(user)
  const isVerified = user?.email_verified === true
  const canJoin = isLoggedIn && isVerified
  const isApprovedMember = myMemberEntry?.status === 'approved'
  const isPendingMember = myMemberEntry?.status === 'pending'
  const squadMemberUsernames = new Set(
    (squad?.members || [])
      .map((member) => member.username)
      .filter(Boolean)
  )
  const visibleSquadActivityEvents = squadActivityEvents.filter(
    (event) => event.current_user_going || event.squad_members_going?.some((username) => squadMemberUsernames.has(username))
  )

  useEffect(() => {
    document.title = squad ? `${squad.name} Squad | KnightLife` : 'KnightLife'
    return () => {
      document.title = 'KnightLife'
    }
  }, [squad])

  const handleJoin = async () => {
    if (!canJoin) return
    try {
      await requestJoin()
    } catch {
      // Hook owns join error state.
    }
  }

  const handleApprove = async (userId) => {
    try {
      await requestApprove(userId)
    } catch (error) {
      alert(getErrorMessage(error, 'Failed to approve member'))
    }
  }

  const handleCopy = async () => {
    const url = window.location.href
    try {
      if (navigator.share) {
        await navigator.share({
          title: 'KnightLife Squad',
          text: `Join my squad! Invite code: ${displayCode}`,
          url,
        })
      } else {
        await navigator.clipboard.writeText(url)
        setCopied(true)
        window.setTimeout(() => setCopied(false), 2000)
      }
    } catch (error) {
      if (error?.name !== 'AbortError') {
        window.prompt('Copy this link to share:', url)
      }
    }
  }

  const handleDelete = async () => {
    try {
      await requestDelete()
      navigate('/squads')
    } catch (error) {
      alert(getErrorMessage(error, 'Failed to delete squad'))
      setConfirmDelete(false)
    }
  }

  const handleBack = (event) => {
    event.preventDefault()
    navigate('/squads')
  }

  return (
    <section className="events-page squads-page">
      <div className="events-page__hero" style={{ paddingBottom: 'var(--space-md)' }}>
        <div className="events-page__hero-bg" aria-hidden />
        <div className="events-page__hero-inner">
          <p className="events-page__badge" style={{ marginBottom: 'var(--space-md)' }}>
            <a href="/squads" onClick={handleBack} style={{ color: 'inherit', textDecoration: 'none' }}>
              ← Squads
            </a>
          </p>

          {loading && (
            <div className="events-page__state" style={{ marginTop: '2rem' }}>
              <div className="events-page__spinner" aria-label="Loading squad" />
              <p>Loading squad...</p>
            </div>
          )}

          {!loading && notFound && (
            <div className="events-page__state events-page__state--error" style={{ marginTop: '2rem' }}>
              <p>Squad not found - check the code and try again.</p>
              <a href="/squads" onClick={handleBack} className="squad-form-card__btn" style={{ display: 'inline-block', marginTop: '1rem' }}>
                Back to Squads
              </a>
            </div>
          )}

          {!loading && squad && (
            <>
              <h1 className="events-page__title" style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'center' }}>
                {squad.name}
                <span className="events-page__badge" style={{ margin: 0, padding: '0.3em 0.8em', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-full)' }}>
                  {squad.is_public ? 'Public' : 'Private'}
                </span>
              </h1>

              <div className="squad-view__code-block">
                <span>{displayCode}</span>
                <button type="button" className="squad-view__copy-btn" onClick={handleCopy}>
                  {copied ? 'Copied!' : 'Copy ↗'}
                </button>
              </div>

              <div className="squad-view__members">
                <h2>
                  {squad.members?.length ?? 0} member{squad.members?.length !== 1 ? 's' : ''}
                  <button
                    type="button"
                    className="squad-view__refresh-btn"
                    onClick={fetchSquad}
                    disabled={loading}
                  >
                    Refresh
                  </button>
                </h2>

                {squad.members && squad.members.length > 0 ? (
                  squad.members.map((member) => (
                    <div key={member.id} className="squad-view__member">
                      <span className="squad-view__member-name">
                        @{member.username ?? `user_${member.user_id}`}
                        {member.status === 'pending' && (
                          <span className="squad-view__owner-badge" style={{ background: '#f59e0b', color: '#111' }}>pending</span>
                        )}
                        {member.user_id === squad.owner_user_id && (
                          <span className="squad-view__owner-badge">owner</span>
                        )}
                        {member.user_id === user?.id && (
                          <span className="squad-view__you-badge">you</span>
                        )}
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        {member.status === 'pending' && user?.id === squad.owner_user_id && (
                          <button
                            className="squad-form-card__btn"
                            style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem', margin: 0 }}
                            onClick={() => handleApprove(member.user_id)}
                          >
                            Approve
                          </button>
                        )}
                        {member.joined_at && (
                          <span className="squad-view__member-date">
                            {new Date(member.joined_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="squad-view__empty">
                    No members yet - share the code to get started.
                  </p>
                )}
              </div>

              <div className="squad-view__activity">
                <h2>Squad Activity</h2>
                {squadActivityLoading ? (
                  <p className="squad-view__empty">Loading squad activity...</p>
                ) : visibleSquadActivityEvents.length > 0 ? (
                  <div className="events-grid">
                    {visibleSquadActivityEvents.map((event) => (
                      <EventCard key={event.id} event={event} />
                    ))}
                  </div>
                ) : (
                  <p className="squad-view__empty">
                    No one in your squad has RSVPed yet.
                  </p>
                )}
              </div>

              <div className="squad-join-area">
                {isApprovedMember ? (
                  <p className="squad-join-area__success">
                    You&apos;re in! Share the code above with your crew.
                  </p>
                ) : isPendingMember ? (
                  <p className="squad-join-area__success" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#b45309' }}>
                    Your request to join is pending approval.
                  </p>
                ) : canJoin ? (
                  <>
                    {joinError && (
                      <p className="squad-form-card__error" style={{ marginBottom: '1rem', width: '100%', maxWidth: '320px', textAlign: 'left' }}>
                        {joinError}
                      </p>
                    )}
                    <button
                      type="button"
                      className="squad-form-card__btn"
                      style={{ fontSize: '1.05rem', padding: '0.6rem 2rem' }}
                      onClick={handleJoin}
                      disabled={joinLoading}
                    >
                      {joinLoading ? '...' : squad.is_public ? `Join as @${username} →` : `Request Access as @${username} →`}
                    </button>
                  </>
                ) : (
                  <div className="squad-auth-gate squad-auth-gate--inline">
                    <p className="squad-auth-gate__msg">
                      {!isLoggedIn
                        ? 'Log in and verify your email to join this squad.'
                        : 'Verify your email to join squads.'}
                    </p>
                    {isLoggedIn ? (
                      <Link to="/profile" className="squad-form-card__btn" style={{ display: 'inline-block', marginTop: '1rem' }}>
                        Verify email →
                      </Link>
                    ) : (
                      <p className="squad-auth-gate__cta">
                        Use the <strong>Sign in</strong> button in the top right.
                      </p>
                    )}
                  </div>
                )}
              </div>

              {user?.id === squad.owner_user_id && (
                <div className="squad-delete-area">
                  {!confirmDelete ? (
                    <button
                      type="button"
                      className="squad-delete-btn"
                      onClick={() => setConfirmDelete(true)}
                    >
                      Delete squad
                    </button>
                  ) : (
                    <div className="squad-delete-confirm">
                      <span>Delete permanently?</span>
                      <button
                        type="button"
                        className="squad-delete-confirm__yes"
                        onClick={handleDelete}
                        disabled={deleteLoading}
                      >
                        {deleteLoading ? '...' : 'Yes, delete'}
                      </button>
                      <button
                        type="button"
                        className="squad-delete-confirm__cancel"
                        onClick={() => setConfirmDelete(false)}
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  )
}
