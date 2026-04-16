import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCreateSquad, useSquadsLandingData } from '../features/squads/hooks'
import './Events.css'
import './Squads.css'

export default function SquadsLanding() {
  const navigate = useNavigate()
  const { user, token } = useAuth()
  const [createName, setCreateName] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [lookupCode, setLookupCode] = useState('')

  const { publicSquads, mySquads } = useSquadsLandingData(token)
  const {
    submit: submitCreate,
    submitting: createLoading,
    error: createError,
  } = useCreateSquad(token)

  const isLoggedIn = Boolean(user)
  const isVerified = user?.email_verified === true
  const canCreate = isLoggedIn && isVerified

  useEffect(() => {
    document.title = 'Squads | KnightLife'
  }, [])

  const handleCreate = async (event) => {
    event.preventDefault()
    if (!createName.trim() || !canCreate) return

    try {
      const data = await submitCreate({ name: createName.trim(), isPublic })
      localStorage.setItem('last_squad_code', data.invite_code)
      navigate(`/squads/${data.invite_code}`)
    } catch {
      // Hook owns error state.
    }
  }

  const handleFind = (event) => {
    event.preventDefault()
    if (!lookupCode.trim()) return
    navigate(`/squads/${lookupCode.trim().toUpperCase()}`)
  }

  return (
    <section className="events-page squads-page">
      <div className="events-page__hero">
        <div className="events-page__hero-bg" aria-hidden />
        <div className="events-page__hero-inner">
          <p className="events-page__badge">Squads</p>
          <h1 className="events-page__title">Show up together.</h1>
          <p className="events-page__subtitle">
            Create a squad, share the code, and see who&apos;s coming.
          </p>
        </div>
      </div>

      <div className="events-page__body" style={{ minHeight: '60vh' }}>
        <div className="squads-landing__grid">
          {isLoggedIn && (
            <div className="squad-form-card" style={{ gridColumn: '1 / -1' }}>
              <h2 className="squad-form-card__title">My Squads</h2>
              {mySquads.length === 0 ? (
                <p className="events-page__subtitle" style={{ margin: 0, fontSize: '0.9rem' }}>
                  You haven&apos;t joined any squads yet.
                </p>
              ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginTop: '0.75rem' }}>
                  {mySquads.map((squad) => (
                    <Link
                      key={squad.id}
                      to={`/squads/${squad.invite_code}`}
                      className="squad-my-card"
                    >
                      <span className="squad-my-card__name">{squad.name}</span>
                      <span className="squad-my-card__meta">
                        {squad.invite_code} &middot; {squad.members.length} {squad.members.length === 1 ? 'member' : 'members'}
                        {squad.owner_user_id === user?.id && ' \u00b7 owner'}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {canCreate ? (
            <form className="squad-form-card" onSubmit={handleCreate}>
              <h2 className="squad-form-card__title">Start a squad</h2>
              {createError && (
                <div className="squad-form-card__error">{createError}</div>
              )}
              <input
                type="text"
                className="squad-form-card__input"
                placeholder="Squad name"
                value={createName}
                onChange={(event) => setCreateName(event.target.value)}
                required
                maxLength={50}
              />
              <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.5rem', marginBottom: '0.5rem', fontSize: '0.95rem', color: 'var(--text-soft)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', userSelect: 'none' }}>
                  <input type="radio" style={{ accentColor: 'var(--ucf-gold)', width: '18px', height: '18px' }} checked={!isPublic} onChange={() => setIsPublic(false)} />
                  Private Squad
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', userSelect: 'none' }}>
                  <input type="radio" style={{ accentColor: 'var(--ucf-gold)', width: '18px', height: '18px' }} checked={isPublic} onChange={() => setIsPublic(true)} />
                  Public Squad
                </label>
              </div>
              <button
                type="submit"
                className="squad-form-card__btn"
                disabled={createLoading}
              >
                {createLoading ? '...' : 'Create squad →'}
              </button>
            </form>
          ) : (
            <div className="squad-form-card squad-auth-gate">
              <h2 className="squad-form-card__title">Start a squad</h2>
              <p className="squad-auth-gate__msg">
                {!isLoggedIn
                  ? 'Sign in and verify your email to create squads.'
                  : 'Verify your email to create squads.'}
              </p>
              {!isLoggedIn ? (
                <p className="squad-auth-gate__cta">
                  Use the <strong>Sign in</strong> button in the top right.
                </p>
              ) : (
                <Link to="/profile" className="squad-form-card__btn" style={{ display: 'block', textAlign: 'center' }}>
                  Go to Profile to verify →
                </Link>
              )}
            </div>
          )}

          <form className="squad-form-card" onSubmit={handleFind}>
            <h2 className="squad-form-card__title">Find a squad</h2>
            <input
              type="text"
              className="squad-form-card__input"
              placeholder="6-character code"
              value={lookupCode}
              onChange={(event) => setLookupCode(event.target.value.toUpperCase())}
              required
              maxLength={6}
            />
            <button type="submit" className="squad-form-card__btn">
              Find squad →
            </button>
          </form>

          <div className="squad-form-card" style={{ gridColumn: '1 / -1' }}>
            <h2 className="squad-form-card__title">Public Squads</h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginTop: '1rem' }}>
              {publicSquads.length === 0 ? (
                <p className="events-page__subtitle" style={{ margin: 0, fontSize: '0.9rem' }}>
                  No public squads right now.
                </p>
              ) : (
                publicSquads.map((squad) => (
                  <Link
                    key={squad.id}
                    to={`/squads/${squad.invite_code}`}
                    className="events-page__filter events-page__filter--active"
                    style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
                  >
                    {squad.name} ({squad.members.length} {squad.members.length === 1 ? 'member' : 'members'}) →
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
