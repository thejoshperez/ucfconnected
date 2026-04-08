"""
Integration smoke test for the Gemini extractor worker.

Pushes a synthetic payload directly into _process_post() (bypassing Redis)
and asserts a correctly populated Event row is written to Postgres.

Requirements: PostgreSQL running, GEMINI_API_KEY in .env, migration from Step 4 completed.
Usage (from backend/): python test_extractor_integration.py
"""
import asyncio
from db.database import AsyncSessionLocal, init_db
from db.models import Event, Post
from workers.extractor_worker import _load_prompt, _process_post
from workers.extractor_worker import _PROMPT_TEMPLATE
import workers.extractor_worker as worker_module
from sqlalchemy import select, delete

TEST_POST_ID = 99999
TEST_PAYLOAD = {
    "post_id": TEST_POST_ID,
    "club_username": "knighthacks_",
    "combined_text": (
        "Join us for Knight Hacks Spring Kickoff!\n"
        "Saturday March 22 2025 at 6:00 PM\n"
        "HEC 101 — Engineering Building 1\n"
        "Free pizza, networking, and project demos."
    ),
    "confidence": 0.93,
}

async def run() -> None:
    await init_db()

    # Load prompt template (worker startup step)
    worker_module._PROMPT_TEMPLATE = _load_prompt()

    # Clean up any leftover test row from a previous run
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Event).where(Event.source_post_id == TEST_POST_ID))
        await session.execute(delete(Post).where(Post.id == TEST_POST_ID))
        mock_post = Post(id=TEST_POST_ID, club_username="knighthacks_", processed=False)
        session.add(mock_post)
        await session.commit()

    # Run extraction
    await _process_post(TEST_PAYLOAD)

    # Assert DB row
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Event).where(Event.source_post_id == TEST_POST_ID)
        )
        event = result.scalar_one_or_none()

        assert event is not None, (
            "No event row written. Check: (1) GEMINI_API_KEY is set, "
            "(2) rso_name column exists (run Step 4 migration), (3) worker logs."
        )
        assert event.title and event.title != "Untitled Event", \
            f"event.title is blank or default: {event.title!r}"
        assert event.rso_name, f"event.rso_name is empty: {event.rso_name!r}"
        assert event.location, f"event.location is empty: {event.location!r}"
        assert event.date, f"event.date is empty: {event.date!r}"
        assert event.club == "knighthacks_", f"event.club wrong: {event.club!r}"

        print("=" * 60)
        print("INTEGRATION TEST: PASSED")
        print(f"  title    : {event.title!r}")
        print(f"  rso_name : {event.rso_name!r}")
        print(f"  location : {event.location!r}")
        print(f"  date     : {event.date!r}")
        print(f"  club     : {event.club!r}")
        print("=" * 60)

        # Clean up test row
        await session.delete(event)
        await session.execute(delete(Post).where(Post.id == TEST_POST_ID))
        await session.commit()
        print("Test row cleaned up.")

asyncio.run(run())
