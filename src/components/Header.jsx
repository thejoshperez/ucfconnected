import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Header.css'

export default function Header() {
  const { pathname } = useLocation()
  const { user, username, login, register, logout, verifyEmail, resendVerification } = useAuth()

  const [showAuthPanel, setShowAuthPanel] = useState(false)
  const [isRegistering, setIsRegistering] = useState(false)
  const [formUser, setFormUser] = useState('')
  const [formPass, setFormPass] = useState('')
  const [formEmail, setFormEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const [verifyCode, setVerifyCode] = useState('')
  const [verifyLoading, setVerifyLoading] = useState(false)
  const [verifyError, setVerifyError] = useState(null)
  const [resendMsg, setResendMsg] = useState(null)

  const panelRef = useRef(null)

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

  const navLink = (to) => {
    const isActive = to === '/'
      ? pathname === '/'
      : pathname === to || pathname.startsWith(to + '/')
    return `nav__link${isActive ? ' nav__link--active' : ''}`
  }

  function openAuth() {
    setError('')
    setFormUser('')
    setFormPass('')
    setFormEmail('')
    setIsRegistering(false)
    setShowAuthPanel(true)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isRegistering) {
        const data = await register(formUser, formPass, formEmail)
        setResendMsg(data.detail || `Verification code sent to ${formEmail}. Check your inbox.`)
        setTimeout(() => setResendMsg(null), 6000)
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

  async function handleVerify() {
    setVerifyLoading(true)
    setVerifyError(null)
    try {
      await verifyEmail(verifyCode)
      setVerifyCode('')
    } catch (err) {
      setVerifyError(err.message)
    } finally {
      setVerifyLoading(false)
    }
  }

  async function handleResend() {
    setVerifyLoading(true)
    setVerifyError(null)
    setResendMsg(null)
    try {
      const data = await resendVerification()
      setResendMsg(data.detail || 'A new verification code is on the way.')
      setTimeout(() => setResendMsg(null), 5000)
    } catch (err) {
      setVerifyError(err.message)
    } finally {
      setVerifyLoading(false)
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
          <Link to="/squads" className={navLink('/squads')}>Squads</Link>
          {username && (
            <Link to="/feed" className={navLink('/feed')}>My Feed</Link>
          )}
          <Link to="/about" className={navLink('/about')}>About</Link>

          <div className="nav__auth" ref={panelRef}>
            {username ? (
              <>
                <Link to="/profile" className="nav__username">
                  @{username}
                  {user && !user.email_verified && (
                    <span className="nav__unverified-dot" title="Email not verified" aria-label="Email not verified" />
                  )}
                </Link>
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
                  {isRegistering && (
                    <input
                      className="auth-panel__input"
                      type="email"
                      placeholder="Email address"
                      autoComplete="email"
                      required
                      value={formEmail}
                      onChange={(e) => setFormEmail(e.target.value)}
                    />
                  )}
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
                    {loading ? '...' : isRegistering ? 'Register' : 'Login'}
                  </button>
                </form>

                <button
                  type="button"
                  className="auth-panel__toggle"
                  onClick={() => { setIsRegistering((p) => !p); setError(''); setFormEmail('') }}
                >
                  {isRegistering
                    ? 'Already have an account? Sign in'
                    : 'No account? Register'}
                </button>
              </div>
            )}
          </div>
        </nav>
      </div>

      {user && !user.email_verified && (
        <div className="verification-banner" role="alert">
          <div className="verification-banner__inner">
            <div className="verification-banner__copy">
              <span className="verification-banner__icon" aria-hidden>Email</span>
              <span className="verification-banner__text">
                Verify your email{user.email ? ` (${user.email})` : ''}. We sent a 6-digit code to your inbox.
              </span>
            </div>
            <div className="verification-banner__controls">
              <input
                className="verification-banner__input"
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                placeholder="6-digit code"
                value={verifyCode}
                onChange={(e) => {
                  setVerifyCode(e.target.value.replace(/\D/g, ''))
                  setVerifyError(null)
                }}
                aria-label="Email verification code"
              />
              <button
                className="verification-banner__btn"
                onClick={handleVerify}
                disabled={verifyCode.length !== 6 || verifyLoading}
              >
                {verifyLoading ? '...' : 'Verify'}
              </button>
              <button
                className="verification-banner__btn verification-banner__btn--ghost"
                onClick={handleResend}
                disabled={verifyLoading}
              >
                Resend
              </button>
            </div>
          </div>
          {verifyError && (
            <p className="verification-banner__error">{verifyError}</p>
          )}
          {resendMsg && (
            <p className="verification-banner__success">{resendMsg}</p>
          )}
        </div>
      )}
    </header>
  )
}
