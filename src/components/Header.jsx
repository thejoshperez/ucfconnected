import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Header.css'

export default function Header() {
  const { pathname } = useLocation()
  const { username, login, register, logout } = useAuth()

  const [showAuthPanel, setShowAuthPanel] = useState(false)
  const [isRegistering, setIsRegistering] = useState(false)
  const [formUser, setFormUser] = useState('')
  const [formPass, setFormPass] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const panelRef = useRef(null)

  // Close the panel when the user clicks outside it
  useEffect(() => {
    if (!showAuthPanel) return
    function handleClickOutside(e) {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setShowAuthPanel(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showAuthPanel])

  // active: exact for '/', prefix for others
  const navLink = (to) => {
    const isActive = to === '/' 
      ? pathname === '/' 
      : (pathname === to || pathname.startsWith(to + '/'));
    return `nav__link${isActive ? ' nav__link--active' : ''}`;
  }

  function openAuth() {
    setError('')
    setFormUser('')
    setFormPass('')
    setIsRegistering(false)
    setShowAuthPanel(true)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isRegistering) {
        await register(formUser, formPass)
      } else {
        await login(formUser, formPass)
      }
      setShowAuthPanel(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="logo">
          <span className="logo__knight">Knight</span>
          <span className="logo__life">Life</span>
        </Link>

        <nav className="nav">
          <Link to="/" className={navLink('/')}>Explore</Link>
          <Link to="/events" className={navLink('/events')}>Events</Link>
          {username && (
            <Link to="/feed" className={navLink('/feed')}>My Feed</Link>
          )}
          <Link to="/about" className={navLink('/about')}>About</Link>

          {/* ── Auth area ── */}
          <div className="nav__auth" ref={panelRef}>
            {username ? (
              <>
                <span className="nav__username">@{username}</span>
                <button
                  type="button"
                  className="nav__link nav__link--cta nav__link--logout"
                  onClick={logout}
                >
                  Logout
                </button>
              </>
            ) : (
              <button
                type="button"
                className="nav__link nav__link--cta"
                onClick={openAuth}
              >
                Sign in
              </button>
            )}

            {showAuthPanel && (
              <div className="auth-panel" role="dialog" aria-label="Sign in or Register">
                <h3 className="auth-panel__title">
                  {isRegistering ? 'Create account' : 'Sign in'}
                </h3>

                {error && <p className="auth-panel__error">{error}</p>}

                <form onSubmit={handleSubmit} className="auth-panel__form">
                  <input
                    className="auth-panel__input"
                    type="text"
                    placeholder="Username"
                    autoComplete="username"
                    required
                    value={formUser}
                    onChange={(e) => setFormUser(e.target.value)}
                  />
                  <input
                    className="auth-panel__input"
                    type="password"
                    placeholder="Password"
                    autoComplete={isRegistering ? 'new-password' : 'current-password'}
                    required
                    value={formPass}
                    onChange={(e) => setFormPass(e.target.value)}
                  />
                  <button
                    type="submit"
                    className="auth-panel__submit"
                    disabled={loading}
                  >
                    {loading ? '…' : isRegistering ? 'Register' : 'Login'}
                  </button>
                </form>

                <button
                  type="button"
                  className="auth-panel__toggle"
                  onClick={() => { setIsRegistering((p) => !p); setError('') }}
                >
                  {isRegistering
                    ? 'Already have an account? Sign in'
                    : "No account? Register"}
                </button>
              </div>
            )}
          </div>
        </nav>
      </div>
    </header>
  )
}
