"""
Instagram scraper built on Instaloader.

Strategy
--------
1. For each club account in settings.CLUB_ACCOUNTS:
   a. Load the profile.
   b. Iterate recent posts up to POST_LIMIT.
   c. Skip posts already in the `posts` table (checked by permalink).
   d. Persist new posts to Postgres.
   e. Enqueue each new post onto the RAW_POSTS_QUEUE for classification.

Rate-limiting
-------------
Instaloader defaults include polite sleep between requests.
For production at scale, use a session cookie (log in once, reuse the
session file) and distribute accounts across multiple scrapers.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timezone

import instaloader
from sqlalchemy import select

from config.settings import get_settings
from db.database import AsyncSessionLocal, init_db
from db.models import Post
from utils.queue import enqueue

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_loader() -> instaloader.Instaloader:
    """
    Create a configured Instaloader instance.

    Auth priority:
      1. Session file (INSTAGRAM_SESSION_FILE) — supports 2FA accounts.
      2. Username + password (no 2FA) — fallback.
      3. Anonymous — very limited, will hit 401s quickly.
    """
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
        request_timeout=30,
    )

    session_file = settings.INSTAGRAM_SESSION_FILE
    username = settings.INSTAGRAM_USERNAME

    # ── Option 1: session file (preferred, works with 2FA) ───────────────
    if session_file and os.path.exists(session_file):
        try:
            loader.load_session_from_file(username, session_file)
            logger.info("Loaded Instagram session from %s", session_file)
            return loader
        except Exception as exc:
            logger.warning("Could not load session file %s: %s — trying password.", session_file, exc)

    # ── Option 2: plain username + password (no 2FA) ─────────────────────
    if username and settings.INSTAGRAM_PASSWORD:
        try:
            loader.login(username, settings.INSTAGRAM_PASSWORD)
            logger.info("Logged into Instagram as %s", username)
            return loader
        except instaloader.exceptions.BadCredentialsException:
            logger.error("Instagram login failed — bad credentials.")
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            logger.error(
                "Instagram login failed — 2FA is enabled. "
                "Run `python login.py` once to save a session file."
            )

    # ── Option 3: anonymous (will likely 401 on most accounts) ───────────
    logger.warning("Scraping as anonymous user — run `python login.py` to authenticate.")
    return loader


async def _permalink_exists(session, permalink: str) -> bool:
    result = await session.execute(select(Post).where(Post.permalink == permalink))
    return result.scalar_one_or_none() is not None


async def scrape_account(loader: instaloader.Instaloader, username: str) -> int:
    """
    Scrape *username*, persist new posts, enqueue them.
    Returns the number of new posts saved.
    """
    logger.info("Scraping @%s …", username)
    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        logger.warning("Profile @%s does not exist — skipping.", username)
        return 0
    except Exception as exc:
        logger.error("Failed to load profile @%s: %s", username, exc)
        return 0

    from datetime import timedelta
    today = datetime.combine(date.today() - timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc)
    new_count = 0
    async with AsyncSessionLocal() as session:
        for post in profile.get_posts():
            if new_count >= settings.POST_LIMIT:
                break

            # Posts come newest-first; stop as soon as we hit something before today
            post_ts = post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc else None
            if post_ts and post_ts < today:
                logger.debug("@%s: reached posts older than today — stopping.", username)
                break

            permalink = f"https://www.instagram.com/p/{post.shortcode}/"
            if await _permalink_exists(session, permalink):
                logger.debug("Post %s already in DB — stopping early for @%s.", permalink, username)
                break

            image_url = post.url if post.url else None
            ts = post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc else None

            db_post = Post(
                club_username=username,
                caption=post.caption,
                timestamp=ts,
                image_url=image_url,
                permalink=permalink,
                processed=False,
            )
            session.add(db_post)
            await session.flush()  # get the auto-generated id

            await enqueue(
                settings.RAW_POSTS_QUEUE,
                {
                    "post_id": db_post.id,
                    "club_username": username,
                    "caption": post.caption,
                    "image_url": image_url,
                    "permalink": permalink,
                },
            )
            new_count += 1
            logger.debug("Saved post id=%d for @%s", db_post.id, username)

        await session.commit()

    logger.info("@%s: %d new post(s) saved and enqueued.", username, new_count)
    return new_count


async def run_scraper() -> None:
    """Entry-point: initialise DB then scrape all configured accounts."""
    await init_db()
    loader = _build_loader()
    total = 0
    for username in settings.CLUB_ACCOUNTS:
        total += await scrape_account(loader, username)
    logger.info("Scrape complete. %d total new posts.", total)
