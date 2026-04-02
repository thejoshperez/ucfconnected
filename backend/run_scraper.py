#!/usr/bin/env python3
"""
Entry-point to run the Instagram scraper once.

Usage:
    python run_scraper.py

Designed to be called by cron every 6 hours:
    0 */6 * * * cd /path/to/backend && python run_scraper.py >> /var/log/knightlife_scraper.log 2>&1
"""
from __future__ import annotations

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

# Ensure the backend root is on the path
import os
sys.path.insert(0, os.path.dirname(__file__))

from scraper.instagram_scraper import run_scraper

if __name__ == "__main__":
    asyncio.run(run_scraper())
