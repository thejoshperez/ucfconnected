"""
Extractor worker — stage 2 of the LLM pipeline.

Pipeline position:  CLASSIFIED_QUEUE → [this worker] → events table

For each dequeued post:
1. Load extractor prompt, substitute OCR+caption text.
2. Call Gemini Flash with a Pydantic response_schema for strict JSON output.
3. Validate response with GeminiExtractedEvent; skip if is_valid_event=False.
4. Write an Event row to Postgres.
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
from functools import partial

from google import genai
from google.genai import types
from pydantic import ValidationError

from config.settings import get_settings
from db.database import AsyncSessionLocal, init_db
from db.models import Event
from models.schemas import GeminiExtractedEvent
from utils.queue import dequeue

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Module-level Gemini client (one instance, reused across all calls) ─────────
_client = genai.Client(api_key=settings.GEMINI_API_KEY)

_STOP = False
_PROMPT_TEMPLATE: str = ""  # loaded once at startup


def _handle_signal(sig, frame) -> None:  # noqa: ANN001
    global _STOP
    _STOP = True
    logger.info("Shutdown signal received — draining then exiting.")


def _load_prompt() -> str:
    """Load extractor_prompt.txt once at startup. Fall back to inline default."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "extractor_prompt.txt")
    try:
        with open(prompt_path) as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("extractor_prompt.txt not found — using inline default.")
        return (
            "Extract event details from the following text and return JSON with fields: "
            "event_name, rso_name, location, start_time, is_valid_event.\n\nText:\n\"\"\"\n{{TEXT}}\n\"\"\""
        )


def _gemini_sync_call(prompt: str) -> str:
    """
    Synchronous Gemini API call — runs inside a thread executor.
    Returns the raw response text string.
    Raises google.genai errors on API failure.
    """
    response = _client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GeminiExtractedEvent,
            temperature=0.1,
        ),
    )
    return response.text


async def _call_gemini(text: str) -> GeminiExtractedEvent | None:
    """
    Call Gemini Flash with retry/backoff.
    Returns a validated GeminiExtractedEvent or None on unrecoverable failure.
    """
    prompt = _PROMPT_TEMPLATE.replace("{{TEXT}}", text[:4000])
    loop = asyncio.get_event_loop()

    for attempt in range(1, settings.GEMINI_MAX_RETRIES + 1):
        try:
            # Run the synchronous SDK call in a thread to avoid blocking the event loop
            raw: str = await loop.run_in_executor(None, partial(_gemini_sync_call, prompt))
            return GeminiExtractedEvent.model_validate_json(raw)

        except ValidationError as exc:
            logger.warning(
                "Gemini response failed schema validation (attempt %d/%d): %s | raw=%r",
                attempt, settings.GEMINI_MAX_RETRIES, exc, raw[:300] if "raw" in dir() else "N/A",
            )
            return None  # Schema failure will not improve on retry

        except Exception as exc:
            exc_str = str(exc)
            is_rate_limit = "429" in exc_str or "quota" in exc_str.lower() or "rate" in exc_str.lower()
            is_timeout = "timeout" in exc_str.lower() or "deadline" in exc_str.lower()

            if (is_rate_limit or is_timeout) and attempt < settings.GEMINI_MAX_RETRIES:
                delay = settings.GEMINI_RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "Gemini %s (attempt %d/%d) — retrying in %.1fs",
                    "rate limit" if is_rate_limit else "timeout",
                    attempt, settings.GEMINI_MAX_RETRIES, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error("Gemini call failed (attempt %d/%d): %s", attempt, settings.GEMINI_MAX_RETRIES, exc)
                return None

    logger.error("All %d Gemini retries exhausted — skipping post.", settings.GEMINI_MAX_RETRIES)
    return None


async def _process_post(payload: dict) -> None:
    post_id: int = payload["post_id"]
    club_username: str = payload.get("club_username", "unknown")
    combined_text: str = payload.get("combined_text") or payload.get("caption") or ""
    confidence: float = float(payload.get("confidence", 0.7))

    if not combined_text:
        logger.warning("Post %d has no text to extract from — skipping.", post_id)
        return

    # ── Gemini extraction ──────────────────────────────────────────────────────
    extracted = await _call_gemini(combined_text)
    if extracted is None:
        logger.warning("Extraction failed for post %d — no DB write.", post_id)
        return

    # ── is_valid_event gate ────────────────────────────────────────────────────
    if not extracted.is_valid_event:
        logger.info("Post %d classified as non-event by Gemini — skipping DB write.", post_id)
        return

    # ── Field mapping to Event ORM model ──────────────────────────────────────
    # GeminiExtractedEvent field → Event column
    #   event_name  → title        (LLM-inferred event title)
    #   rso_name    → rso_name     (human-readable club name from flyer)
    #   location    → location
    #   start_time  → date         (stored as string; existing column name kept)
    #   club_username from queue → club  (Instagram handle, unchanged)
    async with AsyncSessionLocal() as session:
        event = Event(
            club=club_username,
            rso_name=extracted.rso_name or None,
            title=extracted.event_name or "Untitled Event",
            date=extracted.start_time or None,
            location=extracted.location or None,
            confidence=confidence,
            source_post_id=post_id,
        )
        session.add(event)
        await session.commit()
        logger.info(
            "Saved event id=%d: %r | rso=%r | date=%r | @%s (confidence=%.2f)",
            event.id, event.title, event.rso_name, event.date, club_username, confidence,
        )


async def run_extractor_worker() -> None:
    global _PROMPT_TEMPLATE

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set — extractor worker cannot start.")
        return

    _PROMPT_TEMPLATE = _load_prompt()
    await init_db()
    logger.info("Extractor worker started (Gemini/%s). Listening on queue: %s",
                settings.GEMINI_MODEL, settings.CLASSIFIED_QUEUE)

    while not _STOP:
        payload = await dequeue(settings.CLASSIFIED_QUEUE, timeout=5)
        if payload is None:
            continue
        try:
            await _process_post(payload)
        except Exception as exc:
            logger.exception(
                "Unhandled error extracting post %s: %s", payload.get("post_id"), exc
            )

    logger.info("Extractor worker shut down cleanly.")