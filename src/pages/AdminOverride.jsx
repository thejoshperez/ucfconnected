import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function AdminOverride() {
  const [form, setForm] = useState({
    title: '',
    club: '',
    rso_name: '',
    date: '',
    time: '',
    location: '',
    description: '',
    adminKey: '',
  })
  const [status, setStatus] = useState(null)

  function update(field) {
    return (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('Submitting…')

    const { adminKey, ...eventData } = form

    try {
      const res = await fetch(`${API_BASE}/events/admin/inject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-admin-key': adminKey,
        },
        body: JSON.stringify(eventData),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setStatus(`Error ${res.status}: ${err.detail || res.statusText}`)
        return
      }

      const created = await res.json()
      setStatus(`Event #${created.id} created: "${created.title}"`)
      setForm((prev) => ({ ...prev, title: '', description: '', date: '', time: '', location: '', rso_name: '' }))
    } catch (err) {
      setStatus(`Network error: ${err.message}`)
    }
  }

  return (
    <div style={{ maxWidth: 520, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Admin: Inject Featured Event</h1>
      <p style={{ color: '#888', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
        Events injected here appear at the top of the feed (confidence&nbsp;=&nbsp;1.0).
      </p>

      <form onSubmit={handleSubmit}>
        <fieldset style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <legend>Event Details</legend>

          <label>
            Title *
            <input type="text" required value={form.title} onChange={update('title')} style={inputStyle} />
          </label>

          <label>
            Club *
            <input type="text" required value={form.club} onChange={update('club')} style={inputStyle} />
          </label>

          <label>
            RSO Name
            <input type="text" value={form.rso_name} onChange={update('rso_name')} style={inputStyle} />
          </label>

          <label>
            Date
            <input type="text" placeholder="e.g. April 10, 2026" value={form.date} onChange={update('date')} style={inputStyle} />
          </label>

          <label>
            Time
            <input type="text" placeholder="e.g. 6:00 PM" value={form.time} onChange={update('time')} style={inputStyle} />
          </label>

          <label>
            Location
            <input type="text" value={form.location} onChange={update('location')} style={inputStyle} />
          </label>

          <label>
            Description
            <textarea rows={3} value={form.description} onChange={update('description')} style={inputStyle} />
          </label>
        </fieldset>

        <fieldset style={{ border: '1px solid #c00', borderRadius: 8, padding: '1rem', marginTop: '1rem' }}>
          <legend style={{ color: '#c00' }}>Authentication</legend>
          <label>
            Admin Secret Key *
            <input type="password" required value={form.adminKey} onChange={update('adminKey')} style={inputStyle} />
          </label>
        </fieldset>

        <button
          type="submit"
          style={{
            marginTop: '1rem',
            width: '100%',
            padding: '0.75rem',
            background: '#0a0a0a',
            color: '#FFC904',
            border: 'none',
            borderRadius: 8,
            fontWeight: 600,
            fontSize: '1rem',
            cursor: 'pointer',
          }}
        >
          Inject Event
        </button>
      </form>

      {status && (
        <p style={{
          marginTop: '1rem',
          padding: '0.75rem',
          background: status.startsWith('Error') || status.startsWith('Network')
            ? '#fff0f0' : '#f0fff0',
          borderRadius: 8,
          fontSize: '0.875rem',
        }}>
          {status}
        </p>
      )}
    </div>
  )
}

const inputStyle = {
  display: 'block',
  width: '100%',
  padding: '0.5rem',
  marginTop: '0.25rem',
  border: '1px solid #ddd',
  borderRadius: 6,
  fontSize: '0.9rem',
  fontFamily: 'inherit',
  boxSizing: 'border-box',
}
