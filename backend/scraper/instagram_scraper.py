"""
Instagram scraper - self-contained Apify task + Gemini pipeline.

Architecture
------------
1. Run the configured Apify task.
2. Read post items from that task's dataset.
3. For each new post:
   a. Download the image in memory via requests.get.
   b. Send image bytes + caption to Gemini for structured JSON extraction.
   c. If is_valid_event=True -> save a Post and an Event row to Postgres.
   d. If is_valid_event=False -> save a Post row only (dedup anchor).

No Redis queue and no separate extractor worker - the entire pipeline runs
inline from scrape to database commit.
"""
from __future__ import annotations

import asyncio
import logging
import zoneinfo
from datetime import datetime, timezone
from functools import partial

import requests
from apify_client import ApifyClient
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from sqlalchemy import select

from config.settings import get_settings
from db.database import AsyncSessionLocal
from db.models import Event, Post, Follow, User
from utils.email_service import send_calendar_invite

logger = logging.getLogger(__name__)
settings = get_settings()

_NY_TZ = zoneinfo.ZoneInfo("America/New_York")


class EventDetails(BaseModel):
    """Schema enforced on every Gemini extraction call via response_schema."""

    is_valid_event: bool = Field(
        description=(
            "True if this post announces a specific upcoming student event. "
            "False if it is a general announcement, meme, or recap of a past event."
        )
    )
    title: str | None = Field(
        default=None, description="The name or title of the event"
    )
    date: str | None = Field(
        default=None,
        description="The date the event takes place (ISO 8601 preferred, e.g. 2025-04-25)",
    )
    time: str | None = Field(
        default=None, description="The time the event starts (e.g. '7:00 PM')"
    )
    end_time: str | None = Field(
        default=None, description="The time the event ends (e.g. '9:00 PM')"
    )
    location: str | None = Field(
        default=None, description="Where the event is being held"
    )
    description: str | None = Field(
        default=None, description="A short summary of the event"
    )


_DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %I:%M %p",
    "%B %d, %Y %I:%M %p",
    "%m/%d/%Y %I:%M %p",
    "%Y-%m-%d",
    "%B %d, %Y",
    "%m/%d/%Y",
]


def _parse_start_at(date_str: str | None, time_str: str | None) -> datetime | None:
    """Combine Gemini's date + time strings into a timezone-aware NY datetime."""
    if not date_str:
        return None

    raw = date_str.strip()
    if time_str:
        raw = f"{raw} {time_str.strip()}"

    try:
        dt = datetime.fromisoformat(raw[:19])
        return dt.replace(tzinfo=_NY_TZ)
    except (ValueError, OverflowError):
        pass

    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=_NY_TZ)
        except ValueError:
            continue

    logger.debug("Could not parse date/time: date=%r time=%r", date_str, time_str)
    return None


def _normalize_permalink(item: dict) -> str | None:
    permalink = (
        item.get("url")
        or item.get("permalink")
        or item.get("postUrl")
        or item.get("inputUrl")
        or item.get("shortCode")
        or ""
    )
    if permalink and not permalink.startswith("http"):
        permalink = f"https://www.instagram.com/p/{permalink}/"
    return permalink or None


def _extract_owner_username(item: dict) -> str | None:
    owner = item.get("owner")
    if isinstance(owner, dict):
        username = owner.get("username") or owner.get("ownerUsername")
        if username:
            return username

    return (
        item.get("ownerUsername")
        or item.get("username")
        or item.get("profileUsername")
    )


def _extract_image_url(item: dict) -> str | None:
    return (
        item.get("displayUrl")
        or item.get("imageUrl")
        or item.get("display_url")
        or item.get("image_url")
        or item.get("thumbnailUrl")
    )


def _parse_post_timestamp(raw_value) -> datetime | None:
    if raw_value in (None, ""):
        return None

    if isinstance(raw_value, (int, float)):
        try:
            return datetime.fromtimestamp(raw_value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(raw_value, str):
        try:
            normalized = raw_value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None

    return None


async def _permalink_exists(session, permalink: str) -> bool:
    result = await session.execute(select(Post).where(Post.permalink == permalink))
    return result.scalar_one_or_none() is not None


async def _dispatch_auto_invites_for_event(session, event: Event, club_username: str):
    """Notify users who follow this club and have auto-invites enabled."""
    res = await session.execute(
        select(User)
        .join(Follow, Follow.user_id == User.id)
        .where(
            Follow.club_username == club_username,
            User.auto_invites_enabled == True,
            User.email_verified == True,
            User.email.is_not(None)
        )
    )
    followers = res.scalars().all()
    for user in followers:
        try:
            send_calendar_invite(
                user_email=user.email,
                event=event,
                message_body=f"An organization you follow (@{club_username}) just posted a new event."
            )
        except Exception as e:
            logger.warning("Failed to auto-invite user %s for event %s: %s", user.email, event.title, e)


def _download_image(url: str) -> bytes | None:
    """Download image bytes into memory. Returns None on failure."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.content
    except Exception as exc:
        logger.warning("Failed to download image %s: %s", url, exc)
        return None


def _call_gemini_sync(
    client: genai.Client,
    parts: list,
    model: str,
) -> str:
    """Synchronous Gemini call meant to run inside run_in_executor."""
    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EventDetails,
            temperature=0.1,
        ),
    )
    return response.text


async def scrape_instagram_apify() -> int:
    """
    Scrape Instagram via the configured Apify task, extract events with
    Gemini, and write results directly to Postgres.

    Returns the total number of new events saved.
    """
    token = settings.APIFY_API_TOKEN
    if not token:
        logger.error(
            "APIFY_API_TOKEN is not set - cannot scrape Instagram. "
            "Add it to .env to enable this source."
        )
        return 0

    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set - cannot extract events.")
        return 0

    apify = ApifyClient(token)
    gemini = genai.Client(api_key=settings.GEMINI_API_KEY)
    loop = asyncio.get_event_loop()
    task_id = settings.APIFY_INSTAGRAM_TASK_ID

    logger.info("Apify: running task %s ...", task_id)
    try:
        run = apify.task(task_id).call()
    except Exception as exc:
        logger.error("Apify task call failed for %s: %s", task_id, exc)
        return 0

    dataset_id = run.get("defaultDatasetId") if run else None
    if not dataset_id:
        logger.error("Apify task %s finished without a dataset.", task_id)
        return 0

    items = apify.dataset(dataset_id).list_items().items
    logger.info("Apify task %s returned %d item(s).", task_id, len(items))

    total_events = 0
    total_posts = 0

    async with AsyncSessionLocal() as session:
        for item in items:
            permalink = _normalize_permalink(item)
            if not permalink:
                logger.debug("Skipping Apify item without permalink: %r", item)
                continue

            if await _permalink_exists(session, permalink):
                continue

            caption = item.get("caption") or item.get("text") or ""
            image_url = _extract_image_url(item)
            owner = _extract_owner_username(item) or "unknown"
            ts = _parse_post_timestamp(
                item.get("timestamp") or item.get("takenAtTimestamp")
            )

            parts: list = []
            if image_url:
                img_bytes = await loop.run_in_executor(
                    None, partial(_download_image, image_url)
                )
                if img_bytes:
                    parts.append(
                        types.Part.from_bytes(
                            data=img_bytes, mime_type="image/jpeg"
                        )
                    )

            prompt = (
                f"You are analyzing an Instagram post by @{owner}, "
                f"a UCF student organization account.\n\n"
                f"Caption:\n\"\"\"\n{caption[:3000]}\n\"\"\"\n\n"
                "The attached image (if any) is the post's graphic or flyer. "
                "Determine if this post announces a specific upcoming student "
                "event. If it does, extract the event details. "
                "Return JSON matching the schema."
            )
            parts.append(prompt)

            try:
                raw_json = await loop.run_in_executor(
                    None,
                    partial(
                        _call_gemini_sync,
                        gemini,
                        parts,
                        settings.GEMINI_MODEL,
                    ),
                )
                details = EventDetails.model_validate_json(raw_json)
            except Exception as exc:
                logger.warning(
                    "Gemini extraction failed for %s: %s - saving Post only.",
                    permalink,
                    exc,
                )
                session.add(
                    Post(
                        club_username=owner,
                        caption=caption,
                        timestamp=ts,
                        image_url=image_url,
                        permalink=permalink,
                        processed=True,
                    )
                )
                total_posts += 1
                continue

            db_post = Post(
                club_username=owner,
                caption=caption,
                timestamp=ts,
                image_url=image_url,
                permalink=permalink,
                processed=True,
            )
            session.add(db_post)
            await session.flush()
            total_posts += 1

            if not details.is_valid_event:
                logger.debug("Post %s is not an event - skipped.", permalink)
                continue

            event = Event(
                club=owner,
                title=details.title or "Untitled Event",
                date=details.date,
                time=details.time,
                start_at=_parse_start_at(details.date, details.time),
                end_at=_parse_start_at(details.date, details.end_time),
                location=details.location,
                description=details.description,
                confidence=0.85,
                source_post_id=db_post.id,
            )
            session.add(event)
            await session.flush()
            total_events += 1
            
            # Dispatch notifications to followers
            await _dispatch_auto_invites_for_event(session, event, owner)
            
            logger.info(
                "Extracted event from @%s: %r (start_at=%s, end_at=%s)",
                owner,
                event.title,
                event.start_at,
                event.end_at,
            )

        await session.commit()

    logger.info(
        "Instagram pipeline complete. %d post(s) processed, %d event(s) saved.",
        total_posts,
        total_events,
    )
    return total_events
