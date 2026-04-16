import { useState } from 'react'
import { injectAdminEvent } from '../features/events/api'
import { getErrorMessage, isNetworkError } from '../lib/apiClient'
import './AdminOverride.css'

const INITIAL_FORM = {
  title: '',
  club: '',
  rso_name: '',
  date: '',
  time: '',
  location: '',
  description: '',
  adminKey: '',
}

export default function AdminOverride() {
  const [form, setForm] = useState(INITIAL_FORM)
  const [status, setStatus] = useState(null)

  function update(field) {
    return (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus({ tone: 'pending', message: 'Submitting...' })

    const { adminKey, ...eventData } = form

    try {
      const created = await injectAdminEvent(eventData, adminKey)
      setStatus({
        tone: 'success',
        message: `Event #${created.id} created: "${created.title}"`,
      })
      setForm((prev) => ({
        ...prev,
        title: '',
        description: '',
        date: '',
        time: '',
        location: '',
        rso_name: '',
      }))
    } catch (error) {
      setStatus({
        tone: 'error',
        message: isNetworkError(error)
          ? `Network error: ${getErrorMessage(error, 'Could not reach the API.')}`
          : getErrorMessage(error, 'Could not inject the event.'),
      })
    }
  }

  return (
    <div className="admin-override">
      <h1>Admin: Inject Featured Event</h1>
      <p className="admin-override__lede">
        Events injected here appear at the top of the feed.
      </p>

      <form onSubmit={handleSubmit}>
        <fieldset className="admin-override__fieldset">
          <legend>Event Details</legend>

          <label>
            Title *
            <input
              type="text"
              required
              value={form.title}
              onChange={update('title')}
              className="admin-override__input"
            />
          </label>

          <label>
            Club *
            <input
              type="text"
              required
              value={form.club}
              onChange={update('club')}
              className="admin-override__input"
            />
          </label>

          <label>
            RSO Name
            <input
              type="text"
              value={form.rso_name}
              onChange={update('rso_name')}
              className="admin-override__input"
            />
          </label>

          <label>
            Date
            <input
              type="text"
              placeholder="e.g. April 10, 2026"
              value={form.date}
              onChange={update('date')}
              className="admin-override__input"
            />
          </label>

          <label>
            Time
            <input
              type="text"
              placeholder="e.g. 6:00 PM"
              value={form.time}
              onChange={update('time')}
              className="admin-override__input"
            />
          </label>

          <label>
            Location
            <input
              type="text"
              value={form.location}
              onChange={update('location')}
              className="admin-override__input"
            />
          </label>

          <label>
            Description
            <textarea
              rows={3}
              value={form.description}
              onChange={update('description')}
              className="admin-override__input admin-override__textarea"
            />
          </label>
        </fieldset>

        <fieldset className="admin-override__fieldset admin-override__fieldset--danger">
          <legend>Authentication</legend>
          <label>
            Admin Secret Key *
            <input
              type="password"
              required
              value={form.adminKey}
              onChange={update('adminKey')}
              className="admin-override__input"
            />
          </label>
        </fieldset>

        <button type="submit" className="admin-override__submit">
          Inject Event
        </button>
      </form>

      {status && (
        <p className={`admin-override__status admin-override__status--${status.tone}`}>
          {status.message}
        </p>
      )}
    </div>
  )
}
