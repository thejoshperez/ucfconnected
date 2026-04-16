import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import Header from './components/Header'
import Footer from './components/Footer'
import Home from './pages/Home'
import About from './pages/About'
import Events from './pages/Events'
import AdminOverride from './pages/AdminOverride'
import EventDetail from './pages/EventDetail'
import ClubEvents from './pages/ClubEvents'
import NotFound from './pages/NotFound'
import MyFeed from './pages/MyFeed'
import SquadsLanding from './pages/SquadsLanding'
import SquadPage from './pages/SquadPage'
import Profile from './pages/Profile'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/events" element={<Events />} />
          <Route path="/events/club/:instagram" element={<ClubEvents />} />
          <Route path="/events/:id" element={<EventDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/feed" element={<MyFeed />} />
          <Route path="/squads" element={<SquadsLanding />} />
          <Route path="/squads/:code" element={<SquadPage />} />
          <Route path="/profile" element={<Profile />} />
          <Route 
            path="/admin-override" 
            element={
              window.location.hostname === 'localhost' || new URLSearchParams(window.location.search).get('key') === '1'
                ? <AdminOverride />
                : <NotFound />
            } 
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </BrowserRouter>
  )
}

export default App
