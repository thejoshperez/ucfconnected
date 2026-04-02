#!/usr/bin/env python3
"""
Seeds the database with realistic UCF club events so the frontend
shows real-looking data while the scraper hasn't run yet.

Usage: python seed_events.py
"""
from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db.database import AsyncSessionLocal, init_db
from db.models import Post, Event


SAMPLE_POSTS = [
    {
        "club_username": "ucfacm",
        "caption": "🔥 Spring General Meeting TONIGHT! Join us Thursday March 20th at 7:00 PM in HEC 101. We'll be showcasing member projects, voting on next semester's hackathon theme, and handing out ACM t-shirts. Free pizza 🍕 All skill levels welcome!",
        "permalink": "https://www.instagram.com/p/sample001/",
    },
    {
        "club_username": "hack_ucf",
        "caption": "CTF Season is here 🏴 Hack@UCF is hosting an internal Capture The Flag competition on March 22nd, 6:00 PM – 10:00 PM in HEC 450. From beginner web challenges to advanced binary exploitation. Form a team or go solo. Register at the link in our bio!",
        "permalink": "https://www.instagram.com/p/sample002/",
    },
    {
        "club_username": "_ucfai",
        "caption": "🤖 AI Guest Speaker Alert! Join UCF AI this Wednesday, March 19th at 6:30 PM in HEC 356. Dr. Sarah Chen from NVIDIA Research will talk about large-scale transformer training and her career path. Q&A + networking afterwards. Free event, open to all!",
        "permalink": "https://www.instagram.com/p/sample003/",
    },
    {
        "club_username": "gamedevknights",
        "caption": "Spring Game Jam 2025 KICKOFF 🎮 Join us this Friday March 21st at 5:00 PM in HEC 101! Theme reveal at 5:30 PM. You'll have 48 hours to build a game solo or in a team of up to 4. Prizes, food, and fun! All engines welcome (Unity, Godot, Unreal, custom). Sign up in bio.",
        "permalink": "https://www.instagram.com/p/sample004/",
    },
    {
        "club_username": "ucfppms",
        "caption": "Pre-Med Workshop 📚 MCAT Study Strategies with Dr. Rodriguez — Monday March 24th, 7:00 PM, BBS 101. Learn proven test-taking strategies, section breakdowns, and Q&A with a UCF College of Medicine advisor. Free for all members. Non-members welcome for $2.",
        "permalink": "https://www.instagram.com/p/sample005/",
    },
    {
        "club_username": "wibucf",
        "caption": "Women in Business Spring Networking Night 🌟 Connect with UCF alumni at top firms including Deloitte, EY, and JP Morgan. This Thursday March 20th, 6:00 PM in BA1 118. Business casual attire. Bring resumes! RSVP required — link in bio.",
        "permalink": "https://www.instagram.com/p/sample006/",
    },
    {
        "club_username": "ieeeucf",
        "caption": "IEEE Workshop: Intro to PCB Design 🔌 Thursday March 27th, 6:00 PM, ENG1 385. Learn KiCad from scratch, design a simple circuit, and order your own board. Laptops required. Limited to 30 seats — first come first served. Free for IEEE members, $5 for non-members.",
        "permalink": "https://www.instagram.com/p/sample007/",
    },
    {
        "club_username": "isa_ucf",
        "caption": "🌍 International Culture Night 2025 — March 28th at 7:00 PM in the Student Union Pegasus Ballroom! 30+ countries represented, traditional foods, performances, and fashion show. Free admission. Come celebrate the diversity that makes UCF amazing!",
        "permalink": "https://www.instagram.com/p/sample008/",
    },
    {
        "club_username": "ucf.sg",
        "caption": "📢 Student Senate Open Meeting — All students welcome! Join us Tuesday March 25th at 6:30 PM in Student Union 214. We'll be voting on new funding allocations for student orgs and discussing the new parking policy proposal. Make your voice heard!",
        "permalink": "https://www.instagram.com/p/sample009/",
    },
    {
        "club_username": "filmclubucf",
        "caption": "Film Screening Night 🎬 This Wednesday March 19th, 5:30 PM, COMM 101. We're watching Parasite (2019) followed by a director's craft discussion. Bring snacks! We'll also do a short Q&A on our upcoming 48-hour film challenge. All welcome!",
        "permalink": "https://www.instagram.com/p/sample010/",
    },
    {
        "club_username": "ballroomknights",
        "caption": "💃 Beginner Waltz Workshop — No experience needed! This Tuesday March 18th at 8:00 PM in the Student Union Ballroom. Our instructors will teach you the basics of waltz in just one hour. Come solo or bring a partner. Free for members, $3 at the door.",
        "permalink": "https://www.instagram.com/p/sample011/",
    },
    {
        "club_username": "sustainableucf",
        "caption": "🌱 Campus Clean-Up Day! Join Sustainable UCF on Saturday March 22nd at 9:00 AM near the UCF Arboretum. We'll spend 2 hours picking up litter, planting native species, and meeting fellow eco-conscious students. Gloves + bags provided. Just bring yourself!",
        "permalink": "https://www.instagram.com/p/sample012/",
    },
    {
        "club_username": "hsa.ucf",
        "caption": "🎉 HSA Spring Fiesta — Friday March 21st, 7:00 PM, Student Union Multipurpose Room! Live salsa music, traditional Latin food, cultural performances, and raffle prizes. Free entry for UCF students. Bring your student ID. ¡Te esperamos!",
        "permalink": "https://www.instagram.com/p/sample013/",
    },
    {
        "club_username": "ucf_cab",
        "caption": "MOVIE NIGHT UNDER THE STARS 🌟🎥 UCF Campus Activities Board presents: Dune: Part Two on the Reflection Pond lawn! Friday March 21st, 8:30 PM. Free admission, free popcorn. Bring blankets and lawn chairs. Rain date: Saturday March 22nd.",
        "permalink": "https://www.instagram.com/p/sample014/",
    },
    {
        "club_username": "cruatucf",
        "caption": "🙏 Cru Large Group – TONIGHT! Wednesday March 19th at 7:30 PM in Student Union 218. Live worship, message, and community. Theme: 'Finding Purpose in the Chaos of College.' Come as you are — everyone welcome regardless of background!",
        "permalink": "https://www.instagram.com/p/sample015/",
    },
]


SAMPLE_EVENTS = [
    {
        "club": "ucfacm",
        "title": "ACM Spring General Meeting",
        "date": "Thursday, March 20",
        "time": "7:00 PM",
        "location": "HEC 101",
        "description": "Member project showcase, hackathon theme vote, and ACM t-shirt distribution. Free pizza for all attendees.",
        "confidence": 0.97,
        "post_idx": 0,
    },
    {
        "club": "hack_ucf",
        "title": "Internal CTF Competition",
        "date": "Saturday, March 22",
        "time": "6:00 PM – 10:00 PM",
        "location": "HEC 450",
        "description": "Capture the Flag competition with beginner to advanced challenges. Form a team or compete solo. Register via bio link.",
        "confidence": 0.95,
        "post_idx": 1,
    },
    {
        "club": "_ucfai",
        "title": "NVIDIA Research Guest Speaker",
        "date": "Wednesday, March 19",
        "time": "6:30 PM",
        "location": "HEC 356",
        "description": "Dr. Sarah Chen from NVIDIA Research presents on large-scale transformer training. Networking and Q&A to follow.",
        "confidence": 0.93,
        "post_idx": 2,
    },
    {
        "club": "gamedevknights",
        "title": "Spring Game Jam 2025 Kickoff",
        "date": "Friday, March 21",
        "time": "5:00 PM",
        "location": "HEC 101",
        "description": "48-hour game jam with theme reveal, prizes, and food. Teams of up to 4. All engines welcome.",
        "confidence": 0.98,
        "post_idx": 3,
    },
    {
        "club": "ucfppms",
        "title": "MCAT Study Strategies Workshop",
        "date": "Monday, March 24",
        "time": "7:00 PM",
        "location": "BBS 101",
        "description": "Test-taking strategies and section breakdowns with a UCF College of Medicine advisor. Free for members.",
        "confidence": 0.91,
        "post_idx": 4,
    },
    {
        "club": "wibucf",
        "title": "Women in Business Spring Networking Night",
        "date": "Thursday, March 20",
        "time": "6:00 PM",
        "location": "BA1 118",
        "description": "Network with UCF alumni from Deloitte, EY, and JP Morgan. Business casual, bring resumes. RSVP required.",
        "confidence": 0.94,
        "post_idx": 5,
    },
    {
        "club": "ieeeucf",
        "title": "Intro to PCB Design Workshop",
        "date": "Thursday, March 27",
        "time": "6:00 PM",
        "location": "ENG1 385",
        "description": "Learn KiCad from scratch and design your first circuit board. Limited to 30 seats. Bring a laptop.",
        "confidence": 0.92,
        "post_idx": 6,
    },
    {
        "club": "isa_ucf",
        "title": "International Culture Night 2025",
        "date": "Friday, March 28",
        "time": "7:00 PM",
        "location": "Student Union Pegasus Ballroom",
        "description": "30+ countries represented with traditional foods, performances, and a fashion show. Free admission.",
        "confidence": 0.96,
        "post_idx": 7,
    },
    {
        "club": "ucf.sg",
        "title": "Student Senate Open Meeting",
        "date": "Tuesday, March 25",
        "time": "6:30 PM",
        "location": "Student Union 214",
        "description": "Open to all students. Agenda: new funding allocations for student orgs and parking policy proposal vote.",
        "confidence": 0.89,
        "post_idx": 8,
    },
    {
        "club": "filmclubucf",
        "title": "Film Screening: Parasite (2019)",
        "date": "Wednesday, March 19",
        "time": "5:30 PM",
        "location": "COMM 101",
        "description": "Screening of Parasite followed by a director's craft discussion and info about the upcoming 48-hour film challenge.",
        "confidence": 0.88,
        "post_idx": 9,
    },
    {
        "club": "ballroomknights",
        "title": "Beginner Waltz Workshop",
        "date": "Tuesday, March 18",
        "time": "8:00 PM",
        "location": "Student Union Ballroom",
        "description": "One-hour waltz fundamentals class for all experience levels. Come solo or with a partner. Free for members.",
        "confidence": 0.90,
        "post_idx": 10,
    },
    {
        "club": "sustainableucf",
        "title": "Campus Clean-Up Day",
        "date": "Saturday, March 22",
        "time": "9:00 AM",
        "location": "UCF Arboretum",
        "description": "Litter pickup and native species planting near the Arboretum. Gloves and bags provided.",
        "confidence": 0.86,
        "post_idx": 11,
    },
    {
        "club": "hsa.ucf",
        "title": "HSA Spring Fiesta",
        "date": "Friday, March 21",
        "time": "7:00 PM",
        "location": "Student Union Multipurpose Room",
        "description": "Live salsa music, traditional Latin food, cultural performances, and raffle prizes. Free entry with UCF ID.",
        "confidence": 0.93,
        "post_idx": 12,
    },
    {
        "club": "ucf_cab",
        "title": "Movie Night Under the Stars: Dune Part Two",
        "date": "Friday, March 21",
        "time": "8:30 PM",
        "location": "Reflection Pond Lawn",
        "description": "Free outdoor screening of Dune: Part Two. Free popcorn provided. Bring blankets and lawn chairs.",
        "confidence": 0.95,
        "post_idx": 13,
    },
    {
        "club": "cruatucf",
        "title": "Cru Large Group Meeting",
        "date": "Wednesday, March 19",
        "time": "7:30 PM",
        "location": "Student Union 218",
        "description": "Live worship and message on 'Finding Purpose in the Chaos of College.' Everyone welcome.",
        "confidence": 0.87,
        "post_idx": 14,
    },
]


async def seed() -> None:
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy import select, func
        count = await session.execute(select(func.count()).select_from(Event))
        if count.scalar() > 0:
            print("Database already has events — skipping seed.")
            return

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
            event = Event(
                club=e["club"],
                title=e["title"],
                date=e["date"],
                time=e["time"],
                location=e["location"],
                description=e["description"],
                confidence=e["confidence"],
                source_post_id=post.id,
            )
            session.add(event)

        await session.commit()
        print(f"Seeded {len(SAMPLE_POSTS)} posts and {len(SAMPLE_EVENTS)} events.")


if __name__ == "__main__":
    asyncio.run(seed())
