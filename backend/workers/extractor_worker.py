"""
Extractor worker — stage 2 of the LLM pipeline.

Pipeline position:  CLASSIFIED_QUEUE → [this worker] → events table

For each dequeued post:
1. Build a structured extraction prompt.
2. Ask Mistral 7B (via Ollama) to return JSON event fields.
3. Parse the response and write an Event row to Postgres.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import signal

import httpx

from config.settings import get_settings
from db.database import AsyncSessionLocal, init_db
from db.models import Event
from utils.queue import dequeue

logger = logging.getLogger(__name__)
settings = get_settings()

_STOP = False


def _handle_signal(sig, frame):  # noqa: ANN001
    global _STOP
    _STOP = True
    logger.info("Shutdown signal received — draining then exiting.")


async def _call_ollama_extractor(text: str) -> dict:
    """
    Ask Mistral 7B to extract structured event fields from *text*.
    Returns a dict with keys: title, date, time, location, description.
    """
    prompt_path = _prompt_file("extractor_prompt.txt")
    try:
        with open(prompt_path) as f:
            prompt_template = f.read()
    except FileNotFoundError:
        prompt_template = _DEFAULT_EXTRACTOR_PROMPT

    prompt = prompt_template.replace("{{TEXT}}", text[:4000])

    payload = {
        "model": settings.EXTRACTOR_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 300},
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("Ollama extractor error: %s", exc)
        return {}

    raw = data.get("response", "").strip()
    logger.debug("Extractor raw response: %r", raw[:200])
    return _parse_event_json(raw)


def _parse_event_json(raw: str) -> dict:
    """Extract JSON from the LLM response, tolerating surrounding prose."""
    # Try to find the JSON object in the output
    match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if not match:
        logger.warning("Could not find JSON in extractor response: %r", raw[:200])
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        # Try to fix common issues: trailing commas
        cleaned = re.sub(r',\s*([}\]])', r'\1', match.group())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse extractor JSON: %r", raw[:200])
            return {}


async def _process_post(payload: dict) -> None:
    post_id: int = payload["post_id"]
    club_username: str = payload.get("club_username", "unknown")
    combined_text: str = payload.get("combined_text") or payload.get("caption") or ""
    confidence: float = float(payload.get("confidence", 0.7))

    if not combined_text:
        logger.warning("Post %d has no text to extract from — skipping.", post_id)
        return

    # ── LLM extraction ────────────────────────────────────────────────────
    fields = await _call_ollama_extractor(combined_text)
    if not fields:
        logger.warning("Extractor returned empty fields for post %d.", post_id)
        return

    title = fields.get("title", "").strip() or "Untitled Event"
    date = fields.get("date", "").strip() or None
    time = fields.get("time", "").strip() or None
    location = fields.get("location", "").strip() or None
    description = fields.get("description", "").strip() or None

    # ── Persist to DB ─────────────────────────────────────────────────────
    async with AsyncSessionLocal() as session:
        event = Event(
            club=club_username,
            title=title,
            date=date,
            time=time,
            location=location,
            description=description,
            confidence=confidence,
            source_post_id=post_id,
        )
        session.add(event)
        await session.commit()
        logger.info(
            "Saved event id=%d: %r for @%s (confidence=%.2f)",
            event.id,
            title,
            club_username,
            confidence,
        )


async def run_extractor_worker() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    await init_db()
    logger.info("Extractor worker started. Listening on queue: %s", settings.CLASSIFIED_QUEUE)

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


def _prompt_file(name: str) -> str:
    import os
    return os.path.join(os.path.dirname(__file__), "..", "prompts", name)


_DEFAULT_EXTRACTOR_PROMPT = """\
You are an event data extraction assistant for a university campus. Extract structured event details from the following Instagram post text.

Post text:
\"\"\"
{{TEXT}}
\"\"\"

Return ONLY a valid JSON object with exactly these fields (use empty string if a field is not mentioned):
{
  "title": "",
  "date": "",
  "time": "",
  "location": "",
  "description": ""
}

Rules:
- "title": short name of the event (e.g. "Spring General Meeting", "Hackathon Kickoff")
- "date": date in human-readable form (e.g. "March 20", "Thursday March 21, 2025")
- "time": time in 12-hour format (e.g. "6:00 PM", "7:30 PM - 9:00 PM")
- "location": building/room/address (e.g. "Student Union 316", "HEC 101", "Zoom")
- "description": 1-2 sentence summary of the event

Do not include any explanation outside the JSON.
"""
