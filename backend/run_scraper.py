#!/usr/bin/env python3
"""
KnightLife scraping pipeline.

Execution order
---------------
1. Instagram (Apify task + Gemini)
   Runs the configured Apify task, reads image + caption output,
   and sends each post to Gemini for structured event extraction.
   Results go straight to Postgres.

Usage:
    python run_scraper.py

In Docker Compose the run_scraper service handles this automatically on
stack startup. To re-run manually:
    docker compose restart run_scraper
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
from scraper.instagram_scraper import scrape_instagram_apify


async def main() -> None:
    await init_db()

    logger.info("=== Instagram Pipeline (Apify task + Gemini) ===")
    try:
        ig_count = await scrape_instagram_apify()
        logger.info("Instagram produced %d new event(s).", ig_count)
    except Exception:
        logger.exception("Instagram scraper failed.")
        ig_count = 0

    logger.info(
        "============================================================\n"
        "  Pipeline complete.\n"
        "  Instagram     : %d new event(s)\n"
        "============================================================",
        ig_count,
    )

    if ig_count == 0:
        logger.warning(
            "The Instagram pipeline returned 0 results. "
            "The database was NOT populated in this run."
        )


if __name__ == "__main__":
    asyncio.run(main())
