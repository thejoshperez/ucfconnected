# KnightLife

**UCF Campus Event Aggregator** — Discover UCF clubs, follow the ones you care about, and add their events to your Google Calendar. Club meeting details are scraped from Instagram and extracted by AI so you never miss something you actually want to attend.

---

## Features

| Feature | Status |
|---|---|
| Browse 13 UCF clubs with expandable cards | Shipped |
| Follow clubs (requires account) | Shipped |
| Event feed filtered to followed clubs | Shipped |
| All campus events with AI confidence scores | Shipped |
| Filter by Upcoming / Today / All | Shipped |
| One-click Add to Google Calendar | Shipped |
| Share event links (native share / clipboard) | Shipped |
| Individual event detail pages | Shipped |
| Register / sign in (JWT auth) | Shipped |
| Mobile-responsive + installable PWA | Shipped |
| Admin event injection (dev only) | Shipped |

---

## Tech Stack

**Frontend:** React 18 · Vite · React Router v6 · vite-plugin-pwa

**Backend:** Python 3.13 · FastAPI · SQLAlchemy 2.0 async · asyncpg · PostgreSQL 16

**AI Pipeline:** Google Gemini Flash (event extraction) · Phi-3 via Ollama (classifier)

**Infrastructure:** Redis (scrape queue) · Tesseract OCR · Docker Compose

**Auth:** JWT (PyJWT + bcrypt)

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for PostgreSQL + Redis)
- Node.js 18+
- Python 3.13

### 1. Clone and configure

```bash
git clone https://github.com/thejoshperez/ucfconnected.git
cd ucfconnected

# Frontend env
cp .env.local.example .env.local
# Edit .env.local if your backend runs somewhere other than localhost:8000

# Backend env
cp backend/.env.example backend/.env
# Edit backend/.env — at minimum change JWT_SECRET_KEY
```

### 2. Start PostgreSQL and Redis

```bash
docker compose up -d db redis
```

### 3. Start the backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Run the API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

On first start, `init_db()` runs automatically and creates all tables.

### 4. Seed demo data

In a second terminal (with venv active):

```bash
cd backend
python seed_events.py
# → Seeded 13 posts and 13 events.

# To wipe and re-seed:
python seed_events.py --force
```

### 5. Start the frontend

```bash
# From the repo root
npm install
npm run dev
# → http://localhost:5173
```

Open **http://localhost:5173** — you should see 13 club cards and a working events page.

---

## Alternative: Full Docker (API + DB + Redis)

```bash
cp backend/.env.example backend/.env
docker compose up -d

# Seed data (runs against the Dockerized API)
docker compose exec api python seed_events.py

# Frontend still runs outside Docker
npm install && npm run dev
```

---

## Demo Walkthrough

A complete demo takes about 3 minutes:

**1. Club discovery (home page)**
- Land on `/` — 13 UCF club cards load instantly from static data
- Click any card to expand → description, Instagram link, and "See events →" appear
- Click "See events →" for a club (e.g. UCF ACM) → navigates to `/events/club/ucf_acm` with that club's events

**2. Events page**
- Navigate to `/events`
- Switch between Upcoming / Today / All filters
- Search events by title, club, or location
- Click an event card → full detail page at `/events/:id`

**3. Event detail + calendar**
- Detail page shows title, date/time, location, description, and confidence score
- Click **Add to Cal** → Google Calendar opens pre-filled with all fields
- Click **Share ↗** → copies link to clipboard (or native share on mobile)

**4. Auth + personalized feed**
- Click **Sign in** in the header → register a new account (takes 2 seconds)
- Return to home, expand a club card → click **Follow**
- Navigate to `/feed` → events from followed clubs appear
- Follow more clubs → feed updates

**5. About page**
- `/about` explains how the app works

---

## Environment Variables

### Frontend (`.env.local`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

### Backend (`backend/.env`)

**Required to change before demo:**

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Secret for signing JWTs — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_SECRET_KEY` | Key for `/events/admin/inject` endpoint |

**Required for live AI extraction (not needed for seeded demo):**

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key — get one free at [aistudio.google.com](https://aistudio.google.com) |

**Optional:**

| Variable | Default | Description |
|---|---|---|
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `INSTAGRAM_USERNAME` | — | IG account for authenticated scraping |
| `INSTAGRAM_PASSWORD` | — | IG account password |
| `CLUB_ACCOUNTS` | — | Comma-separated Instagram handles to scrape |
| `DATABASE_URL` | local postgres | Override with Docker service name in containers |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |

---

## Routes

| Path | Description |
|---|---|
| `/` | Club discovery — browse and follow UCF RSOs |
| `/events` | All campus events (upcoming / today / all) |
| `/events/:id` | Individual event detail + add-to-cal |
| `/events/club/:instagram` | Events filtered to one club |
| `/feed` | Personalized feed (requires sign-in) |
| `/about` | About KnightLife |
| `/admin-override` | Manual event injection (localhost only) |

---

## API Reference

```
GET  /events                    All events (sorted by confidence desc)
GET  /events/upcoming           Events from the last 14 days
GET  /events/today              Events matching today's date
GET  /events/{id}               Single event by ID
GET  /events/club/{instagram}   Events for one club (case-insensitive)

POST /auth/register             Create account → returns JWT
POST /auth/login                Verify credentials → returns JWT
POST /auth/follow/{club}        Follow a club (Bearer token required)
GET  /auth/follows              List followed clubs (Bearer token required)

POST /events/admin/inject       Inject a featured event (x-admin-key header)

GET  /health                    Health check
GET  /docs                      Interactive API docs (Swagger UI)
```

---

## Project Structure

```
ucfconnected/
├── src/                    # React frontend
│   ├── components/         # Header, Footer, ClubCard, EventCard, Hero, ...
│   ├── context/            # AuthContext (JWT + follow state)
│   ├── data/               # clubs.js (static club data)
│   └── pages/              # Home, Events, EventDetail, ClubEvents, MyFeed, About
├── backend/
│   ├── api/
│   │   ├── main.py         # FastAPI app + CORS + lifespan
│   │   └── routes/         # events.py, auth.py, squads.py
│   ├── db/
│   │   ├── models.py       # Post, Event, User, Follow
│   │   └── database.py     # Async SQLAlchemy session
│   ├── workers/            # extractor_worker.py, classifier_worker.py
│   ├── seed_events.py      # Demo data seeder (--force to re-seed)
│   └── requirements.txt
├── docker-compose.yml      # PostgreSQL + Redis + API
└── .env.local.example      # Frontend env template
```

---

## License

MIT
