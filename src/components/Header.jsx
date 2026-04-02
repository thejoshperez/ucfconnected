import { Link, useLocation } from 'react-router-dom'
import './Header.css'

export default function Header() {
  const { pathname } = useLocation()

  const navLink = (to) =>
    `nav__link${pathname === to ? ' nav__link--active' : ''}`

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="logo">
          <span className="logo__knight">Knight</span>
          <span className="logo__life">Life</span>
        </Link>
        <nav className="nav">
          <Link to="/" className={navLink('/')}>
            Explore
          </Link>
          <Link to="/events" className={navLink('/events')}>
            Events
          </Link>
          <Link to="/about" className={navLink('/about')}>
            About
          </Link>
          <a href="#signin" className="nav__link nav__link--cta">Sign in</a>
        </nav>
      </div>
    </header>
  )
}
