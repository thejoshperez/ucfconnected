#!/usr/bin/env python3
"""
KnightLife — Anti-fragile scraping pipeline.

Execution order:
  1. KnightConnect (base layer — always runs first, highly stable)
  2. Instagram / Instaloader (primary — may fail due to rate limits)
  3. Instagram / Apify (failover — triggered only if step 2 fails)

Usage:
    python run_scraper.py

Designed to be called by cron every 6 hours:
    0 */6 * * * cd /path/to/backend && python run_scraper.py >> /var/log/knightlife_scraper.log 2>&1
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

# Ensure the backend root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from db.database import init_db
from scraper.knightconnect_scraper import scrape_knightconnect_events
from scraper.instagram_scraper import run_scraper as run_instagram_primary
from scraper.instagram_scraper import run_scraper_apify as run_instagram_apify


async def main() -> None:
    await init_db()

    # ── Phase 1: KnightConnect base layer ────────────────────────────────
    logger.info("═══ Phase 1/2: KnightConnect (base layer) ═══")
    try:
        kc_count = await scrape_knightconnect_events()
        logger.info("KnightConnect produced %d new post(s).", kc_count)
    except Exception:
        logger.exception("KnightConnect scraper failed unexpectedly.")
        kc_count = 0

    # ── Phase 2: Instagram (primary → Apify failover) ────────────────────
    logger.info("═══ Phase 2/2: Instagram ═══")
    ig_count = 0
    apify_used = False

    try:
        ig_count = await run_instagram_primary()
        logger.info("Instagram (Instaloader) produced %d new post(s).", ig_count)
    except Exception:
        logger.exception(
            "Instagram primary scraper (Instaloader) failed. "
            "Activating Apify failover …"
        )
        ig_count = 0

    # Trigger Apify failover if primary returned nothing or threw
    if ig_count == 0:
        if ig_count == 0 and not apify_used:
            logger.warning(
                "Primary Instagram scraper returned 0 results. "
                "Activating Apify failover …"
            )
        try:
            apify_count = await run_instagram_apify()
            apify_used = True
            ig_count = apify_count
            logger.info("Apify failover produced %d new post(s).", apify_count)
        except Exception:
            logger.exception("Apify failover also failed.")

    # ── Summary ──────────────────────────────────────────────────────────
    total = kc_count + ig_count
    logger.info(
        "══════════════════════════════════════════════════════════════\n"
        "  Pipeline complete.\n"
        "  KnightConnect : %d new post(s)\n"
        "  Instagram     : %d new post(s)%s\n"
        "  TOTAL         : %d\n"
        "══════════════════════════════════════════════════════════════",
        kc_count,
        ig_count,
        " (via Apify)" if apify_used else "",
        total,
    )

    if total == 0:
        logger.warning(
            "⚠ All scrapers returned 0 results. "
            "The database was NOT populated in this run."
        )


if __name__ == "__main__":
    asyncio.run(main())
