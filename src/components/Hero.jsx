import './Hero.css'

export default function Hero({ searchValue, onSearchChange }) {
  return (
    <section className="hero">
      <div className="hero__bg" aria-hidden />
      <div className="hero__inner">
        <p className="hero__badge">University of Central Florida</p>
        <h1 className="hero__title">
          Find your crew.
          <br />
          <span className="hero__title-accent">Never miss a meeting.</span>
        </h1>
        <p className="hero__subtitle">
          Discover clubs, add meetings to your calendar, and stay connected with Knight Life.
        </p>
        <div className="hero__search-wrap">
          <span className="hero__search-icon" aria-hidden>⌕</span>
          <input
            type="search"
            className="hero__search"
            placeholder="Search clubs by name, interest, or keyword…"
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            aria-label="Search clubs"
          />
        </div>
      </div>
    </section>
  )
}
