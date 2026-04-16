# KnightLife

**UCF Campus Event Aggregator** — Discover UCF clubs, follow the ones you care about, and add their events to your Google Calendar. Club meeting details are scraped from Instagram and extracted by AI so you never miss something you actually want to attend.

---

## Inspiration
It's surprisingly hard for college students to find out what's going on around campus. Most announcements are scattered across different social media platforms, mostly Instagram, which creates a messy and noisy experience.

## What it does
KnightLife is a central hub for campus events. You can browse clubs, follow organizations you care about, see their events compiled on a dedicated feed, and add events straight to Google Calendar. We also added "Squads", allowing you to form private friend groups to see exactly who in your circle is attending what events!

## How we built it
The frontend was built using React and Vite, delivering a fast PWA-ready experience. The backend uses a robust Python FastAPI + PostgreSQL architecture. At the heart of the app is our automation pipeline: we scrape university club Instagram pages with Apify, feed the post image and caption context directly into **Google Gemini 2.0 Flash** to extract strict, structured JSON data using native Pydantic schemas, and store everything in our database automatically. 

## Challenges we ran into
Extracting event data (date, time, title, location) from Instagram flyers and abstract Gen-Z captions in a heavily unstructured format was incredibly difficult, but Google Gemini was excellent. Furthermore, figuring out how to build the "Squad context" dynamically on our public-facing event endpoints required some creative FastAPI dependency injections and efficient SQL query joining.

## Accomplishments that we're proud of
We are proud to have built a full-stack, deployed, production-ready system with a totally automated AI ingestion pipeline. Our Squad attendance feature maps seamlessly over an intuitive UI to make KnightLife highly engaging.

## What we learned
We learned the power of standardizing structured AI outputs! We also learned how to use FastAPI dependency injections efficiently alongside SQLAlchemy schemas to quickly surface contextual data without the deadly N+1 query problem.

## What's next for KnightLife
Moving forward we'd like to integrate direct push notifications and potentially host the platform as a real source of truth for our university!

---

## Features

| Feature | Status |
|---|---|
| Browse 13 UCF clubs with expandable cards | Shipped |
| Follow clubs (requires account) | Shipped |
| Event feed filtered to followed clubs | Shipped |
| All campus events with AI confidence scores | Shipped |
| Filter by Upcoming / Today / All | Shipped |
| Squads: Create/join private groups via invite codes | Shipped |
| Contextual squad attendance badges | Shipped |
| One-click Add to Google Calendar | Shipped |
| Share event links (native share / clipboard) | Shipped |
| Individual event detail pages | Shipped |
| Register / sign in (JWT auth + email verification) | Shipped |
| Mobile-responsive + installable PWA | Shipped |

---

## Tech Stack

**Frontend:** React 18 · Vite · React Router v6 · vite-plugin-pwa

**Backend:** Python 3.13 · FastAPI · SQLAlchemy 2.0 async · asyncpg · PostgreSQL 16

**AI Pipeline:** Google Gemini 2.0 Flash (vision + text extraction)

**Infrastructure:** Apify (Instagram Scraper) · Docker Compose

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

**5. Squads (Viral Mechanics)**
- Navigate to `/squads` → create a squad or join one using a 6-character code
- Open an event card and click "RSVP" → see your squad members' attendance contextualized!

**6. About page**
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
| `APIFY_API_TOKEN` | — | Apify token for executing scraper |
| `APIFY_INSTAGRAM_TASK_ID` | — | Task ID for the linked apify actor |
| `DATABASE_URL` | local postgres | Override with Docker service name in containers |
| `REDIS_URL` | `redis://localhost:6379/0` | Optional Redis connection string |

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
│   └── pages/              # Home, Events, EventDetail, ClubEvents, MyFeed, Squads
├── backend/
│   ├── api/
│   │   ├── main.py         # FastAPI app + CORS + lifespan
│   │   └── routes/         # events.py, auth.py, squads.py
│   ├── db/
│   │   ├── models.py       # Post, Event, User, Follow, Squad, SquadMember
│   │   └── database.py     # Async SQLAlchemy session
│   ├── scraper/            # instagram_scraper.py (Apify task execution)
│   ├── seed_events.py      # Demo data seeder (--force to re-seed)
│   └── requirements.txt
├── docker-compose.yml      # PostgreSQL + Redis + API
└── .env.local.example      # Frontend env template
```

---

## License

MIT
