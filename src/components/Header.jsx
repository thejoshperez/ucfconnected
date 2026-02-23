import { Link, useLocation } from 'react-router-dom'
import './Header.css'

export default function Header() {
  const location = useLocation()
  const isAbout = location.pathname === '/about'

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="logo">
          <span className="logo__knight">Knight</span>
          <span className="logo__life">Life</span>
        </Link>
        <nav className="nav">
          <Link to="/" className={`nav__link ${!isAbout ? 'nav__link--active' : ''}`}>
            Explore
          </Link>
          <Link to="/about" className={`nav__link ${isAbout ? 'nav__link--active' : ''}`}>
            About
          </Link>
          <a href="#signin" className="nav__link nav__link--cta">Sign in</a>
        </nav>
      </div>
    </header>
  )
}
