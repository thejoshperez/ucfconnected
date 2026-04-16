import { useState } from 'react'
import { Navigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Profile.css'

function Toggle({ checked, onChange, id }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      id={id}
      className={`profile-toggle${checked ? ' profile-toggle--on' : ''}`}
      onClick={() => onChange(!checked)}
    >
      <span className="profile-toggle__thumb" />
    </button>
  )
}

function SettingRow({ label, description, checked, onChange, id }) {
  return (
    <label htmlFor={id} className="profile-setting">
      <div className="profile-setting__text">
        <span className="profile-setting__label">{label}</span>
        <span className="profile-setting__desc">{description}</span>
      </div>
      <Toggle checked={checked} onChange={onChange} id={id} />
    </label>
  )
}

export default function Profile() {
  const { user, username, logout, updateUserSettings, verifyEmail, resendVerification } = useAuth()

  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState(null)
  const [verifyCode, setVerifyCode] = useState('')
  const [verifyLoading, setVerifyLoading] = useState(false)
  const [verifyError, setVerifyError] = useState(null)
  const [resendMsg, setResendMsg] = useState(null)

  if (!user) {
    return <Navigate to="/" replace />
  }

  async function handleToggle(field, value) {
    setSaving(true)
    setSaveMsg(null)
    await updateUserSettings({ [field]: value })
    setSaving(false)
    setSaveMsg('Saved')
    setTimeout(() => setSaveMsg(null), 2000)
  }

  async function handleVerify(e) {
    e.preventDefault()
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
      setTimeout(() => setResendMsg(null), 6000)
    } catch (err) {
      setVerifyError(err.message)
    } finally {
      setVerifyLoading(false)
    }
  }

  const initials = username ? username.slice(0, 2).toUpperCase() : '??'

  return (
    <div className="profile-page">
      <div className="profile-page__hero">
        <div className="profile-avatar" aria-hidden>{initials}</div>
        <div className="profile-hero__info">
          <h1 className="profile-hero__username">@{username}</h1>
          <p className="profile-hero__email">
            {user.email ?? <span className="profile-hero__email--missing">No email set</span>}
          </p>
        </div>
      </div>

      <div className="profile-page__body">
        <section className="profile-card">
          <h2 className="profile-card__title">Account</h2>

          <div className="profile-field">
            <span className="profile-field__label">Username</span>
            <span className="profile-field__value">{username}</span>
          </div>

          <div className="profile-field">
            <span className="profile-field__label">Email</span>
            <span className="profile-field__value">{user.email ?? '-'}</span>
          </div>

          <div className="profile-field">
            <span className="profile-field__label">Verification</span>
            {user.email_verified ? (
              <span className="profile-badge profile-badge--verified">Verified</span>
            ) : (
              <span className="profile-badge profile-badge--unverified">Not verified</span>
            )}
          </div>

          {!user.email_verified && (
            <div className="profile-verify">
              <p className="profile-verify__hint">
                Enter the 6-digit code from your inbox.
              </p>
              <form className="profile-verify__form" onSubmit={handleVerify}>
                <input
                  className="profile-verify__input"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  placeholder="000000"
                  value={verifyCode}
                  onChange={(e) => {
                    setVerifyCode(e.target.value.replace(/\D/g, ''))
                    setVerifyError(null)
                  }}
                  aria-label="Verification code"
                />
                <button
                  type="submit"
                  className="profile-verify__btn"
                  disabled={verifyCode.length !== 6 || verifyLoading}
                >
                  {verifyLoading ? '...' : 'Verify'}
                </button>
                <button
                  type="button"
                  className="profile-verify__btn profile-verify__btn--ghost"
                  onClick={handleResend}
                  disabled={verifyLoading}
                >
                  Resend code
                </button>
              </form>
              {verifyError && <p className="profile-verify__error">{verifyError}</p>}
              {resendMsg && <p className="profile-verify__success">{resendMsg}</p>}
            </div>
          )}
        </section>

        <section className="profile-card">
          <div className="profile-card__title-row">
            <h2 className="profile-card__title">Notifications</h2>
            {saving && <span className="profile-card__saving">Saving...</span>}
            {saveMsg && !saving && <span className="profile-card__saved">{saveMsg}</span>}
          </div>

          <SettingRow
            id="auto-invites"
            label="Auto calendar invites"
            description="Automatically send calendar invites when you RSVP to an event."
            checked={user.auto_invites_enabled ?? true}
            onChange={(val) => handleToggle('auto_invites_enabled', val)}
          />

          <SettingRow
            id="notify-squad"
            label="Notify squad on RSVP"
            description="Let your squad know when you mark yourself as attending an event."
            checked={user.notify_squad_on_rsvp ?? true}
            onChange={(val) => handleToggle('notify_squad_on_rsvp', val)}
          />
        </section>

        <section className="profile-card profile-card--links">
          <Link to="/feed" className="profile-link">My Event Feed {'->'}</Link>
          <Link to="/squads" className="profile-link">My Squads &rarr;</Link>
        </section>

        <section className="profile-card profile-card--danger">
          <h2 className="profile-card__title">Session</h2>
          <button type="button" className="profile-logout-btn" onClick={logout}>
            Log out of @{username}
          </button>
        </section>
      </div>
    </div>
  )
}
