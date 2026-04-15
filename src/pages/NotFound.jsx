import { Link, useLocation } from 'react-router-dom'

export default function NotFound() {
  const { pathname } = useLocation()
  
  return (
    <div style={{ maxWidth: 680, margin: '6rem auto', padding: '0 1rem', textAlign: 'center' }}>
      <h1>Page not found</h1>
      <p style={{ margin: '1rem 0 2rem', color: 'var(--color-text-secondary, #666)' }}>
        No route matches <code style={{ background: '#eee', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>{pathname}</code>
      </p>
      <Link to="/" className="nav__link nav__link--cta" style={{ display: 'inline-block', textDecoration: 'none' }}>
        Go home
      </Link>
    </div>
  )
}
