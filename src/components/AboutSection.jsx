import { Link } from 'react-router-dom'
import './AboutSection.css'

export default function AboutSection() {
  return (
    <section className="about">
      <div className="about__content">
        <p className="about__eyebrow">Why Knight Life</p>
        <h2 className="about__title">
          Connection is essential to the human experience.
        </h2>
        <div className="about__body">
          <p>
            College is more than classes and credits. It’s where you find your people, the ones who share your interests, push you to grow, and show up when it matters. At the University of Central Florida, that happens in clubs: in weekly meetings, at events, and in the moments in between.
          </p>
          <p>
            Knight Life exists so you never have to choose between staying connected and staying on top of your schedule. Discover clubs, add meetings to your calendar, and show up. Because the best parts of UCF happen when we’re together.
          </p>
        </div>
        <p className="about__tagline">Find your crew. Never miss a meeting.</p>
      </div>

      <div className="about__section about__section--alt">
        <div className="about__block">
          <h3 className="about__heading">How it works</h3>
          <ul className="about__steps">
            <li>
              <span className="about__step-num">1</span>
              <div>
                <strong>Discover.</strong> Browse clubs by interest, from tech and arts to leadership and recreation. See meeting times, locations, and what each club is about.
              </div>
            </li>
            <li>
              <span className="about__step-num">2</span>
              <div>
                <strong>Add to your calendar.</strong> One click sends club meetings straight to your Google Calendar. No more screenshotting an Instagram post and forgetting.
              </div>
            </li>
            <li>
              <span className="about__step-num">3</span>
              <div>
                <strong>Show up.</strong> Get reminders, sync with your schedule, and actually be there. The rest is connection.
              </div>
            </li>
            <li>
              <span className="about__step-num">4</span>
              <div>
                <strong>Create squads.</strong> Form or join small groups with other Knights who go to the same club. Invite friends, see who’s in your squad, and show up together, so you never walk in alone.
              </div>
            </li>
          </ul>
        </div>
      </div>

      <div className="about__section">
        <div className="about__block about__block--narrow">
          <h3 className="about__heading">Built for Knights</h3>
          <p className="about__body about__body--standalone">
            UCF is one of the largest universities in the nation. With so many people and so many clubs, it’s easy to lose track, or never find your fit in the first place. Knight Life puts every club in one place and makes it simple to stay on top of meetings. Whether you’re in one club or five, we’re here so you can focus on showing up, not on remembering when.
          </p>
        </div>
      </div>

      <div className="about__section about__section--alt">
        <div className="about__block about__block--narrow">
          <h3 className="about__heading">Our mission</h3>
          <p className="about__body about__body--standalone">
            We believe that belonging matters. Knight Life exists to help every UCF student find their community and stay connected, without the stress of a scattered schedule. By bridging clubs and calendars, we want to make it easier to say yes to the things that matter most.
          </p>
        </div>
      </div>

      <div className="about__cta">
        <p className="about__cta-text">Ready to find your crew?</p>
        <Link to="/" className="about__cta-btn">Explore clubs</Link>
      </div>
    </section>
  )
}
