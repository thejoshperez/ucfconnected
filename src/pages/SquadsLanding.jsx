import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import './Events.css'
import './Squads.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function SquadsLanding() {
  const navigate = useNavigate()
  const location = useLocation()

  const [createName, setCreateName] = useState('')
  const [createLoading, setCreateLoading] = useState(false)
  const [createError, setCreateError] = useState(null)

  const [lookupCode, setLookupCode] = useState('')

  useEffect(() => {
    document.title = 'Squads | KnightLife'

    const recent = localStorage.getItem('last_squad_code')
    if (recent && !location.state?.skipAutoRedirect) {
      navigate(`/squads/${recent}`, { replace: true })
    }
  }, [navigate, location])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!createName.trim()) return

    setCreateLoading(true)
    setCreateError(null)

    try {
      const res = await fetch(`${API_BASE}/squads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: createName.trim() })
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to create squad')
      }

      localStorage.setItem('last_squad_code', data.invite_code)
      navigate(`/squads/${data.invite_code}`)

    } catch (err) {
      setCreateError(err.message)
    } finally {
      setCreateLoading(false)
    }
  }

  const handleFind = (e) => {
    e.preventDefault()
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
            Create a squad, share the code, and see who's coming.
          </p>
        </div>
      </div>

      <div className="events-page__body" style={{ minHeight: '60vh' }}>
        <div className="squads-landing__grid">

          <form className="squad-form-card" onSubmit={handleCreate}>
            <h2 className="squad-form-card__title">Start a squad</h2>
            {createError && <div className="squad-form-card__error">{createError}</div>}
            <input
              type="text"
              className="squad-form-card__input"
              placeholder="Squad name"
              value={createName}
              onChange={e => setCreateName(e.target.value)}
              required
              maxLength={50}
            />
            <button
              type="submit"
              className="squad-form-card__btn"
              disabled={createLoading}
            >
              {createLoading ? '…' : 'Create squad \u2192'}
            </button>
          </form>

          <form className="squad-form-card" onSubmit={handleFind}>
            <h2 className="squad-form-card__title">Find a squad</h2>
            <input
              type="text"
              className="squad-form-card__input"
              placeholder="6-character code"
              value={lookupCode}
              onChange={e => setLookupCode(e.target.value.toUpperCase())}
              required
              maxLength={6}
            />
            <button
              type="submit"
              className="squad-form-card__btn"
            >
              Find squad \u2192
            </button>
          </form>

        </div>
      </div>
    </section>
  )
}
