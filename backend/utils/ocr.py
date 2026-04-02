"""
OCR pipeline using Tesseract via pytesseract.

Downloads the post image to a temporary directory and extracts text.
The resulting text is appended to the caption before LLM processing,
which helps when clubs post event details only as flyer images.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import httpx
import pytesseract
from PIL import Image

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Allow override of tesseract binary path via config
if settings.TESSERACT_CMD and settings.TESSERACT_CMD != "tesseract":
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


async def extract_text_from_url(image_url: str) -> str:
    """
    Download *image_url* and return OCR-extracted text.
    Returns an empty string on any failure so the caller can still
    proceed with caption-only processing.
    """
    if not image_url:
        return ""

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(image_url)
            response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = Path(tmp.name)

        try:
            text = _run_ocr(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        cleaned = _clean_ocr_text(text)
        logger.debug("OCR extracted %d chars from %s", len(cleaned), image_url[:60])
        return cleaned

    except Exception as exc:
        logger.warning("OCR failed for %s: %s", image_url[:60], exc)
        return ""


def _run_ocr(image_path: Path) -> str:
    """Run Tesseract on the given image file."""
    img = Image.open(image_path)
    # Pre-process: convert to greyscale for better accuracy
    img = img.convert("L")
    return pytesseract.image_to_string(img, config="--psm 3")


def _clean_ocr_text(text: str) -> str:
    """Strip noise characters and collapse whitespace."""
    lines = [line.strip() for line in text.splitlines()]
    # Drop lines that are pure punctuation or very short
    meaningful = [ln for ln in lines if len(ln) > 2 and not _is_noise(ln)]
    return "\n".join(meaningful)


def _is_noise(line: str) -> bool:
    non_alpha = sum(1 for c in line if not (c.isalpha() or c.isspace()))
    return non_alpha / max(len(line), 1) > 0.7
