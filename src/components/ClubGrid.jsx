import './ClubGrid.css'
import ClubCard from './ClubCard'

export default function ClubGrid({ clubs, categories, category, onCategoryChange }) {
  return (
    <section className="club-grid-section" id="explore">
      <div className="club-grid-section__inner">
        <div className="club-grid-section__head">
          <h2 className="club-grid-section__title">Explore clubs</h2>
          <div className="club-grid-section__filters" role="tablist" aria-label="Filter by category">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                role="tab"
                aria-selected={category === cat}
                className={`club-grid-section__filter ${category === cat ? 'club-grid-section__filter--active' : ''}`}
                onClick={() => onCategoryChange(cat)}
              >
                {cat === 'all' ? 'All' : cat}
              </button>
            ))}
          </div>
        </div>
        {clubs.length === 0 ? (
          <p className="club-grid-section__empty">No clubs match your search. Try a different keyword or category.</p>
        ) : (
          <div className="club-grid">
            {clubs.map((club) => (
              <ClubCard key={club.id} club={club} />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
