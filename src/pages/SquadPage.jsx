import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './Events.css'
import './Squads.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function SquadPage() {
  const { code } = useParams()
  const displayCode = code.toUpperCase()
  const navigate = useNavigate()

  const [squad, setSquad] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  
  const [joinName, setJoinName] = useState('')
  const [joinLoading, setJoinLoading] = useState(false)
  const [joinError, setJoinError] = useState(null)
  const [joined, setJoined] = useState(false)
  
  const [copied, setCopied] = useState(false)

  const fetchSquad = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/squads/${displayCode}`)
      if (res.status === 404) {
        setNotFound(true)
        return
      }
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const data = await res.json()
      setSquad(data)
      localStorage.setItem('last_squad_code', displayCode)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [displayCode])

  useEffect(() => {
    fetchSquad()
  }, [fetchSquad])

  useEffect(() => {
    if (squad) {
      document.title = `${squad.name} Squad | KnightLife`
    } else {
      document.title = 'KnightLife'
    }
    return () => { document.title = 'KnightLife' }
  }, [squad])

  const handleJoin = async (e) => {
    e.preventDefault()
    if (!joinName.trim()) return

    setJoinLoading(true)
    setJoinError(null)

    try {
      const res = await fetch(`${API_BASE}/squads/${displayCode}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ member_name: joinName.trim() })
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to join squad')
      }

      setSquad(data)
      setJoined(true)
    } catch (err) {
      setJoinError(err.message)
    } finally {
      setJoinLoading(false)
    }
  }

  const handleCopy = async () => {
    const url = window.location.href
    try {
      if (navigator.share) {
        await navigator.share({
          title: 'KnightLife Squad',
          text: `Join my squad! Invite code: ${displayCode}`,
          url: url
        })
      } else {
        await navigator.clipboard.writeText(url)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
      }
    } catch (err) {
      if (err && err.name !== 'AbortError') {
        const fallback = prompt('Copy this link to share:', url)
        if (fallback) setCopied(true)
      }
    }
  }

  const handleBack = (e) => {
    e.preventDefault()
    // Pass state avoiding instant redirection to stale profiles
    navigate('/squads', { state: { skipAutoRedirect: true } })
  }

  return (
    <section className="events-page squads-page">
      <div className="events-page__hero" style={{ paddingBottom: 'var(--space-md)' }}>
        <div className="events-page__hero-bg" aria-hidden />
        <div className="events-page__hero-inner">
          <p className="events-page__badge" style={{ marginBottom: 'var(--space-md)' }}>
            <a href="/squads" onClick={handleBack} style={{ color: 'inherit', textDecoration: 'none' }}>
              &larr; Squads
            </a>
          </p>

          {loading && (
            <div className="events-page__state" style={{ marginTop: '2rem' }}>
              <div className="events-page__spinner" aria-label="Loading squad" />
              <p>Loading squad…</p>
            </div>
          )}

          {!loading && notFound && (
            <div className="events-page__state events-page__state--error" style={{ marginTop: '2rem' }}>
              <p>Squad not found \u2014 check the code and try again.</p>
              <a href="/squads" onClick={handleBack} className="squad-form-card__btn" style={{ display: 'inline-block', marginTop: '1rem' }}>Back to Squads</a>
            </div>
          )}

          {!loading && squad && (
            <>
              <h1 className="events-page__title" style={{ marginBottom: '0.5rem' }}>{squad.name}</h1>
              
              <div className="squad-view__code-block">
                <span>{displayCode}</span>
                <button type="button" className="squad-view__copy-btn" onClick={handleCopy}>
                  {copied ? 'Copied!' : 'Copy \u2197'}
                </button>
              </div>

              <div className="squad-view__members">
                <h2>
                  {squad.members?.length || 0} member{(squad.members?.length !== 1) ? 's' : ''}
                  <button type="button" className="squad-view__refresh-btn" onClick={fetchSquad} disabled={loading}>
                    Refresh
                  </button>
                </h2>
                
                {squad.members && squad.members.length > 0 ? (
                  squad.members.map((m, idx) => (
                    <div key={idx} className="squad-view__member">
                      <span>&bull; {m.member_name}</span>
                      {m.joined_at && (
                        <span className="squad-view__member-date">
                          {new Date(m.joined_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="squad-view__empty">No members yet \u2014 share the code to get started.</p>
                )}
              </div>

              {!joined ? (
                <div style={{ maxWidth: 400, margin: '0 auto', textAlign: 'left' }}>
                  <form className="squad-form-card" onSubmit={handleJoin} style={{ padding: 'var(--space-lg)' }}>
                    <h3 className="squad-form-card__title" style={{ margin: 0, fontSize: '1.05rem' }}>Join this squad</h3>
                    {joinError && <div className="squad-form-card__error">{joinError}</div>}
                    <input
                      type="text"
                      className="squad-form-card__input"
                      placeholder="Your name"
                      value={joinName}
                      onChange={e => setJoinName(e.target.value)}
                      required
                      maxLength={50}
                    />
                    <button type="submit" className="squad-form-card__btn" disabled={joinLoading}>
                      {joinLoading ? '…' : 'Join \u2192'}
                    </button>
                  </form>
                </div>
              ) : (
                <p style={{ marginTop: '2rem', fontSize: '0.95rem', color: 'var(--text)', fontWeight: 600 }}>
                  You're in! Share the code above with your crew.
                </p>
              )}
            </>
          )}

        </div>
      </div>
    </section>
  )
}
