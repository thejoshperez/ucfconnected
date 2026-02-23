import { Link } from 'react-router-dom'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <div className="footer__brand">
          <span className="footer__logo">Knight Life</span>
          <p className="footer__tagline">Connect to clubs. Add to calendar. Show up.</p>
        </div>
        <div className="footer__links">
          <Link to="/">Explore clubs</Link>
          <Link to="/about">About</Link>
          <a href="#contact">Contact</a>
        </div>
        <p className="footer__ucf">University of Central Florida</p>
      </div>
    </footer>
  )
}
