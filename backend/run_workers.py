#!/usr/bin/env python3
"""
Runs the classifier and extractor workers concurrently in a single process.

Usage:
    python run_workers.py

For production, run each worker as a separate process (or container) so
they can scale independently:
    python -m workers.classifier_worker
    python -m workers.extractor_worker
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

import os
sys.path.insert(0, os.path.dirname(__file__))

from workers.classifier_worker import run_classifier_worker
from workers.extractor_worker import run_extractor_worker


async def main() -> None:
    await asyncio.gather(
        run_classifier_worker(),
        run_extractor_worker(),
    )


if __name__ == "__main__":
    asyncio.run(main())
