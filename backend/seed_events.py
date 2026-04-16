#!/usr/bin/env python3
"""
Seeds the database with realistic UCF club events so the frontend
shows real-looking data while the scraper hasn't run yet.

Usage:
    python seed_events.py           # skip if events already exist
    python seed_events.py --force   # drop existing events and re-seed
"""
from __future__ import annotations

import asyncio
import sys
import os
import zoneinfo
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from db.database import AsyncSessionLocal, init_db
from db.models import Post, Event

_NY_TZ = zoneinfo.ZoneInfo("America/New_York")


def _make_date_str(days_ahead: int) -> str:
    """Return a human-readable date string like 'Monday, April 21' relative to today."""
    d = (datetime.now(_NY_TZ) + timedelta(days=days_ahead)).date()
    return f"{d.strftime('%A, %B')} {d.day}"


def _make_start_at(days_ahead: int, time_str: str | None) -> datetime | None:
    """Build a timezone-aware NY datetime from a relative day offset + HH:MM AM/PM string."""
    if not time_str:
        return None
    # Take only the start portion from ranges like "6:00 PM – 10:00 PM"
    time_part = time_str.split("–")[0].strip().split("-")[0].strip()
    d = (datetime.now(_NY_TZ) + timedelta(days=days_ahead)).date()
    try:
        dt = datetime.strptime(f"{d.isoformat()} {time_part}", "%Y-%m-%d %I:%M %p")
        return dt.replace(tzinfo=_NY_TZ)
    except ValueError:
        return None

# ── All instagram handles match clubs.js exactly ─────────────────────────────

SAMPLE_POSTS = [
    # ── Student Government & Campus Life ───────────────────────────────────
    {
        "club_username": "ucf_sga",
        "caption": "📢 Student Senate Open Meeting — All students welcome! Join us Tuesday April 22nd at 7:00 PM in Student Union 214. We'll be voting on new funding allocations for student orgs and discussing the new parking policy proposal. Make your voice heard!",
        "permalink": "https://www.instagram.com/p/sample001/",
    },
    {
        "club_username": "ucfcab",
        "caption": "MOVIE NIGHT UNDER THE STARS 🌟🎥 UCF Campus Activities Board presents: Dune: Part Two on the Reflection Pond lawn! Friday April 25th, 8:30 PM. Free admission, free popcorn. Bring blankets and lawn chairs. Rain date: Saturday April 26th.",
        "permalink": "https://www.instagram.com/p/sample002/",
    },
    {
        "club_username": "ucfosi",
        "caption": "🏛️ Spring Org Fair is BACK — Wednesday April 23rd, 11:00 AM – 2:00 PM on Memory Mall! Browse tables from 100+ RSOs, meet members, and find your next club. Perfect for students who haven't found their people yet. See you there!",
        "permalink": "https://www.instagram.com/p/sample003/",
    },
    {
        "club_username": "knightthonucf",
        "caption": "💛 Knight-Thon Pre-Marathon Kickoff 🎉 Join us Thursday April 24th at 7:30 PM in the RWC multipurpose room! Learn what to expect at the 20-hour dance marathon, meet your fundraising team, and get hyped. Free food and Knight-Thon merch giveaway!",
        "permalink": "https://www.instagram.com/p/sample004/",
    },

    # ── Tech, CS & Engineering ─────────────────────────────────────────────
    {
        "club_username": "hackucf",
        "caption": "CTF Season is here 🏴 Hack@UCF is hosting an internal Capture The Flag competition on April 26th, 6:00 PM – 10:00 PM in HEC 450. From beginner web challenges to advanced binary exploitation. Form a team or go solo. Register at the link in our bio!",
        "permalink": "https://www.instagram.com/p/sample005/",
    },
    {
        "club_username": "knighthacks",
        "caption": "🚀 Workshop: Deploying Full-Stack Apps with Docker & Railway — Friday April 25th at 6:00 PM in Engineering 1 Room 106. We'll containerize a React + FastAPI project and deploy it live during the session. Laptops required. Free for everyone!",
        "permalink": "https://www.instagram.com/p/sample006/",
    },
    {
        "club_username": "ucf_acm",
        "caption": "🔥 Spring General Meeting TONIGHT! Join us Tuesday April 22nd at 6:00 PM in HEC 101. We'll be showcasing member projects, voting on next semester's hackathon theme, and handing out ACM t-shirts. Free pizza 🍕 All skill levels welcome!",
        "permalink": "https://www.instagram.com/p/sample007/",
    },
    {
        "club_username": "ucfthetatau",
        "caption": "⚙️ Theta Tau Professional Dev Night — Monday April 21st at 7:00 PM in ENG2 203. Three UCF alumni from SpaceX, Lockheed Martin, and Siemens will discuss engineering career paths. Resume reviews available after the panel. Open to all engineering students.",
        "permalink": "https://www.instagram.com/p/sample008/",
    },
    {
        "club_username": "ieee_ucf",
        "caption": "IEEE Workshop: Intro to PCB Design 🔌 Thursday April 24th, 6:00 PM, ENG1 385. Learn KiCad from scratch, design a simple circuit, and order your own board. Laptops required. Limited to 30 seats — first come first served. Free for IEEE members, $5 for non-members.",
        "permalink": "https://www.instagram.com/p/sample009/",
    },
    {
        "club_username": "gamedevknights",
        "caption": "Spring Game Jam 2025 KICKOFF 🎮 Join us this Friday April 25th at 5:00 PM in HEC 101! Theme reveal at 5:30 PM. You'll have 48 hours to build a game solo or in a team of up to 4. Prizes, food, and fun! All engines welcome (Unity, Godot, Unreal, custom). Sign up in bio.",
        "permalink": "https://www.instagram.com/p/sample010/",
    },

    # ── Business, Pre-Professional & Service ──────────────────────────────
    {
        "club_username": "wibucf",
        "caption": "Women in Business Spring Networking Night 🌟 Connect with UCF alumni at top firms including Deloitte, EY, and JP Morgan. This Wednesday April 23rd, 6:30 PM in BA1 119. Business casual attire. Bring resumes! RSVP required — link in bio.",
        "permalink": "https://www.instagram.com/p/sample011/",
    },
    {
        "club_username": "ucfamsa",
        "caption": "📚 MCAT Study Strategies Workshop with Dr. Rodriguez — Monday April 21st, 7:00 PM, HPA1 106. Learn proven test-taking strategies, section breakdowns, and Q&A with a UCF College of Medicine advisor. Free for all members. Non-members welcome for $2.",
        "permalink": "https://www.instagram.com/p/sample012/",
    },
    {
        "club_username": "volunteerucf",
        "caption": "🌱 Spring Service Day! Join Volunteer UCF on Saturday April 26th at 9:00 AM at the Second Harvest Food Bank in Orlando. We'll spend 3 hours sorting food donations for Central Florida families. Transportation from campus provided. Sign up at the link in bio — spots limited!",
        "permalink": "https://www.instagram.com/p/sample013/",
    },
]


SAMPLE_EVENTS = [
    # ── Student Government & Campus Life ───────────────────────────────────
    {
        "club": "ucf_sga",
        "title": "Student Senate Open Meeting",
        "days_ahead": 1,
        "time": "7:00 PM",
        "location": "Student Union 214",
        "description": "Open to all UCF students. Agenda: new funding allocations for student orgs and parking policy proposal vote. Make your voice heard.",
        "confidence": 0.92,
        "post_idx": 0,
    },
    {
        "club": "ucfcab",
        "title": "Movie Night Under the Stars: Dune Part Two",
        "days_ahead": 4,
        "time": "8:30 PM",
        "location": "Reflection Pond Lawn",
        "description": "Free outdoor screening of Dune: Part Two with free popcorn. Bring blankets and lawn chairs.",
        "confidence": 0.95,
        "post_idx": 1,
    },
    {
        "club": "ucfosi",
        "title": "Spring RSO Org Fair",
        "days_ahead": 2,
        "time": "11:00 AM",
        "location": "Memory Mall",
        "description": "Browse tables from 100+ Registered Student Organizations. Perfect for students looking to get involved in campus life.",
        "confidence": 0.96,
        "post_idx": 2,
    },
    {
        "club": "knightthonucf",
        "title": "Knight-Thon Pre-Marathon Kickoff",
        "days_ahead": 3,
        "time": "7:30 PM",
        "location": "RWC Multipurpose Room",
        "description": "Learn what to expect at the 20-hour dance marathon, meet your fundraising team, and get hyped for the event. Free food and merch giveaway.",
        "confidence": 0.93,
        "post_idx": 3,
    },

    # ── Tech, CS & Engineering ─────────────────────────────────────────────
    {
        "club": "hackucf",
        "title": "Internal CTF Competition",
        "days_ahead": 5,
        "time": "6:00 PM",
        "location": "HEC 450",
        "description": "Capture the Flag competition with challenges from beginner web to advanced binary exploitation. Form a team or compete solo.",
        "confidence": 0.95,
        "post_idx": 4,
    },
    {
        "club": "knighthacks",
        "title": "Workshop: Deploying Full-Stack Apps with Docker & Railway",
        "days_ahead": 4,
        "time": "6:00 PM",
        "location": "Engineering 1 Room 106",
        "description": "Containerize a React + FastAPI project and deploy it live during the session. Bring a laptop. Free for all skill levels.",
        "confidence": 0.94,
        "post_idx": 5,
    },
    {
        "club": "ucf_acm",
        "title": "ACM Spring General Meeting",
        "days_ahead": 1,
        "time": "6:00 PM",
        "location": "HEC 101",
        "description": "Member project showcase, hackathon theme vote, and ACM t-shirt distribution. Free pizza for all attendees.",
        "confidence": 0.97,
        "post_idx": 6,
    },
    {
        "club": "ucfthetatau",
        "title": "Theta Tau Engineering Alumni Panel",
        "days_ahead": 0,
        "time": "7:00 PM",
        "location": "ENG2 203",
        "description": "UCF alumni from SpaceX, Lockheed Martin, and Siemens discuss engineering career paths. Resume reviews available after the panel.",
        "confidence": 0.91,
        "post_idx": 7,
    },
    {
        "club": "ieee_ucf",
        "title": "Intro to PCB Design Workshop",
        "days_ahead": 3,
        "time": "6:00 PM",
        "location": "ENG1 385",
        "description": "Learn KiCad from scratch and design your first circuit board. Limited to 30 seats. Bring a laptop. Free for IEEE members, $5 otherwise.",
        "confidence": 0.92,
        "post_idx": 8,
    },
    {
        "club": "gamedevknights",
        "title": "Spring Game Jam Kickoff",
        "days_ahead": 4,
        "time": "5:00 PM",
        "location": "HEC 101",
        "description": "48-hour game jam with theme reveal at 5:30 PM. Teams up to 4. Prizes, food, and fun. All engines welcome (Unity, Godot, Unreal).",
        "confidence": 0.98,
        "post_idx": 9,
    },

    # ── Business, Pre-Professional & Service ──────────────────────────────
    {
        "club": "wibucf",
        "title": "Women in Business Spring Networking Night",
        "days_ahead": 2,
        "time": "6:30 PM",
        "location": "BA1 119",
        "description": "Network with UCF alumni from Deloitte, EY, and JP Morgan. Business casual attire, bring resumes. RSVP required via bio link.",
        "confidence": 0.94,
        "post_idx": 10,
    },
    {
        "club": "ucfamsa",
        "title": "MCAT Study Strategies Workshop",
        "days_ahead": 0,
        "time": "7:00 PM",
        "location": "HPA1 106",
        "description": "Test-taking strategies and section breakdowns with a UCF College of Medicine advisor. Free for members, $2 for non-members.",
        "confidence": 0.91,
        "post_idx": 11,
    },
    {
        "club": "volunteerucf",
        "title": "Spring Service Day: Second Harvest Food Bank",
        "days_ahead": 5,
        "time": "9:00 AM",
        "location": "Second Harvest Food Bank, Orlando",
        "description": "3-hour volunteer shift sorting food donations for Central Florida families. Transportation from campus provided. Limited spots.",
        "confidence": 0.90,
        "post_idx": 12,
    },
]


async def seed(force: bool = False) -> None:
    await init_db()

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func, delete

        count_result = await session.execute(select(func.count()).select_from(Event))
        existing_count = count_result.scalar()

        if existing_count > 0 and not force:
            print(f"Database already has {existing_count} events — skipping seed.")
            print("Run with --force to drop and re-seed.")
            return

        if force and existing_count > 0:
            await session.execute(delete(Event))
            await session.execute(delete(Post))
            await session.commit()
            print(f"Dropped {existing_count} existing events and their posts.")

        # Insert posts
        posts = []
        for p in SAMPLE_POSTS:
            post = Post(
                club_username=p["club_username"],
                caption=p["caption"],
                permalink=p["permalink"],
                processed=True,
            )
            session.add(post)
            posts.append(post)
        await session.flush()

        # Insert events
        for e in SAMPLE_EVENTS:
            post = posts[e["post_idx"]]
            days_ahead = e.get("days_ahead", 0)
            event = Event(
                club=e["club"],
                title=e["title"],
                date=_make_date_str(days_ahead),
                time=e.get("time"),
                start_at=_make_start_at(days_ahead, e.get("time")),
                location=e.get("location"),
                description=e.get("description"),
                confidence=e["confidence"],
                source_post_id=post.id,
            )
            session.add(event)

        await session.commit()
        print(f"Seeded {len(SAMPLE_POSTS)} posts and {len(SAMPLE_EVENTS)} events.")
        print("Clubs covered:", ", ".join(sorted(set(e["club"] for e in SAMPLE_EVENTS))))


if __name__ == "__main__":
    force = "--force" in sys.argv
    asyncio.run(seed(force=force))
