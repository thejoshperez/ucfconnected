"""
Classifier worker — stage 1 of the LLM pipeline.

Pipeline position:  RAW_POSTS_QUEUE → [this worker] → CLASSIFIED_QUEUE

For each dequeued post:
1. Run the cheap keyword pre-filter.
2. If it passes, OCR the image and merge text with the caption.
3. Ask Phi-3 (via Ollama) whether the post is an event announcement.
4. If confident enough, push to CLASSIFIED_QUEUE for the extractor.
5. Mark the post as processed in Postgres regardless of outcome.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import signal
import sys

import httpx
from sqlalchemy import select

from config.settings import get_settings
from db.database import AsyncSessionLocal, init_db
from db.models import Post
from utils.keyword_filter import is_event_candidate
from utils.ocr import extract_text_from_url
from utils.queue import dequeue, enqueue

logger = logging.getLogger(__name__)
settings = get_settings()

_STOP = False


def _handle_signal(sig, frame):  # noqa: ANN001
    global _STOP
    logger.info("Shutdown signal received — draining queue then exiting.")
    _STOP = True


async def _call_ollama_classifier(text: str) -> tuple[bool, float]:
    """
    Ask Phi-3 to classify *text* as an event announcement or not.
    Returns (is_event, confidence_0_to_1).
    """
    prompt_path = _prompt_file("classifier_prompt.txt")
    try:
        with open(prompt_path) as f:
            prompt_template = f.read()
    except FileNotFoundError:
        prompt_template = _DEFAULT_CLASSIFIER_PROMPT

    prompt = prompt_template.replace("{{TEXT}}", text[:3000])

    payload = {
        "model": settings.CLASSIFIER_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 60},
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("Ollama classifier error: %s", exc)
        return False, 0.0

    raw = data.get("response", "").strip().lower()
    logger.debug("Classifier raw response: %r", raw)

    # Expected format: JSON like {"is_event": true, "confidence": 0.92}
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            is_event = bool(parsed.get("is_event", False))
            confidence = float(parsed.get("confidence", 0.5))
            return is_event, confidence
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: look for yes/no
    is_event = "yes" in raw or '"is_event": true' in raw
    confidence = 0.7 if is_event else 0.3
    return is_event, confidence


async def _process_post(payload: dict) -> None:
    post_id: int = payload["post_id"]
    caption: str | None = payload.get("caption")
    image_url: str | None = payload.get("image_url")
    club_username: str = payload.get("club_username", "unknown")

    # ── 1. Keyword pre-filter ─────────────────────────────────────────────
    if not is_event_candidate(caption):
        logger.debug("Post %d failed keyword filter — skipping LLM.", post_id)
        await _mark_processed(post_id)
        return

    # ── 2. OCR (if image available) ───────────────────────────────────────
    ocr_text = ""
    if image_url:
        ocr_text = await extract_text_from_url(image_url)

    combined_text = _merge_texts(caption, ocr_text)

    # ── 3. LLM classification ─────────────────────────────────────────────
    is_event, confidence = await _call_ollama_classifier(combined_text)
    logger.info(
        "Post %d classified: is_event=%s confidence=%.2f", post_id, is_event, confidence
    )

    # ── 4. Forward to extractor if confident ─────────────────────────────
    if is_event and confidence >= settings.MIN_CONFIDENCE:
        await enqueue(
            settings.CLASSIFIED_QUEUE,
            {
                **payload,
                "combined_text": combined_text,
                "confidence": confidence,
            },
        )

    # ── 5. Mark as processed ──────────────────────────────────────────────
    await _mark_processed(post_id)


async def _mark_processed(post_id: int) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post:
            post.processed = True
            await session.commit()


def _merge_texts(caption: str | None, ocr: str) -> str:
    parts = []
    if caption:
        parts.append(caption.strip())
    if ocr:
        parts.append(f"[Image text]: {ocr.strip()}")
    return "\n\n".join(parts)


def _prompt_file(name: str) -> str:
    import os
    return os.path.join(os.path.dirname(__file__), "..", "prompts", name)


async def run_classifier_worker() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    await init_db()
    logger.info("Classifier worker started. Listening on queue: %s", settings.RAW_POSTS_QUEUE)

    while not _STOP:
        payload = await dequeue(settings.RAW_POSTS_QUEUE, timeout=5)
        if payload is None:
            continue
        try:
            await _process_post(payload)
        except Exception as exc:
            logger.exception("Unhandled error processing post %s: %s", payload.get("post_id"), exc)

    logger.info("Classifier worker shut down cleanly.")


_DEFAULT_CLASSIFIER_PROMPT = """\
You are an event detection assistant for a university campus. Analyse the following Instagram post text and determine whether it is announcing an upcoming event, meeting, workshop, seminar, or social gathering.

Post text:
\"\"\"
{{TEXT}}
\"\"\"

Respond ONLY with valid JSON in this exact format:
{"is_event": true, "confidence": 0.95}

Where:
- "is_event" is true if the post is announcing an event, false otherwise.
- "confidence" is a float between 0.0 and 1.0 indicating your certainty.
"""
