"""
KnightConnect scraper — the "base layer" data source.

Scrapes the public UCF KnightConnect events page for structured event data
(title, date/time, location). This source is highly stable because it is
an official UCF system that does not require authentication.

Returns Post-compatible dicts that can be persisted via the standard pipeline.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from config.settings import get_settings
from db.database import AsyncSessionLocal
from db.models import Post
from utils.queue import enqueue

logger = logging.getLogger(__name__)
settings = get_settings()

KNIGHTCONNECT_URL = "https://knightconnect.campuslabs.com/engage/events"
SOURCE_TAG = "knightconnect"


async def _permalink_exists(session, permalink: str) -> bool:
    result = await session.execute(select(Post).where(Post.permalink == permalink))
    return result.scalar_one_or_none() is not None


def _parse_events_page(html: str) -> list[dict]:
    """
    Parse the KnightConnect events listing page and return a list of
    raw event dicts.

    Each dict has keys: title, date_text, location, permalink, image_url.
    The exact CSS selectors may need adjustment if KnightConnect redesigns
    their frontend.
    """
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []

    # KnightConnect renders event cards; each card links to a detail page.
    # Selector targets the event card container — adjust if DOM changes.
    for card in soup.select("div[class*='event'], a[href*='/engage/event/']"):
        link_tag = card if card.name == "a" else card.find("a", href=True)
        if not link_tag or "/engage/event/" not in link_tag.get("href", ""):
            continue

        href = link_tag["href"]
        if href.startswith("/"):
            href = f"https://knightconnect.campuslabs.com{href}"

        title_tag = card.find(["h2", "h3", "span"])
        title = title_tag.get_text(strip=True) if title_tag else "Untitled Event"

        # Date and location are often in secondary spans/divs
        meta_tags = card.find_all(["p", "span", "div"])
        date_text = ""
        location = ""
        for tag in meta_tags:
            text = tag.get_text(strip=True)
            if not text or text == title:
                continue
            # Heuristic: first non-title text is usually the date,
            # second is location
            if not date_text:
                date_text = text
            elif not location:
                location = text
                break

        img_tag = card.find("img")
        image_url = img_tag["src"] if img_tag and img_tag.get("src") else None

        events.append({
            "title": title,
            "date_text": date_text,
            "location": location,
            "permalink": href,
            "image_url": image_url,
        })

    return events


async def scrape_knightconnect_events() -> int:
    """
    Fetch the KnightConnect events page, parse it, persist new events
    as Post rows, and enqueue them for classification.

    Returns the number of new posts saved.
    """
    logger.info("Scraping KnightConnect events page …")

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(KNIGHTCONNECT_URL)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to fetch KnightConnect: %s", exc)
        return 0

    raw_events = _parse_events_page(resp.text)
    if not raw_events:
        logger.warning("KnightConnect returned 0 parseable events — page structure may have changed.")
        return 0

    logger.info("Parsed %d events from KnightConnect.", len(raw_events))

    new_count = 0
    async with AsyncSessionLocal() as session:
        for ev in raw_events:
            permalink = ev["permalink"]
            if await _permalink_exists(session, permalink):
                logger.debug("KnightConnect event already in DB: %s", permalink)
                continue

            # Build a caption from the structured fields so the downstream
            # classifier/extractor pipeline can process it identically to
            # an Instagram post.
            caption = f"{ev['title']}\n{ev['date_text']}\n{ev['location']}".strip()

            db_post = Post(
                club_username=SOURCE_TAG,
                caption=caption,
                timestamp=datetime.now(timezone.utc),
                image_url=ev.get("image_url"),
                permalink=permalink,
                processed=False,
            )
            session.add(db_post)
            await session.flush()

            await enqueue(
                settings.RAW_POSTS_QUEUE,
                {
                    "post_id": db_post.id,
                    "club_username": SOURCE_TAG,
                    "caption": caption,
                    "image_url": ev.get("image_url"),
                    "permalink": permalink,
                },
            )
            new_count += 1
            logger.debug("Saved KnightConnect event id=%d: %s", db_post.id, ev["title"])

        await session.commit()

    logger.info("KnightConnect: %d new event(s) saved and enqueued.", new_count)
    return new_count
