"""
Cheap, rule-based pre-filter applied before LLM calls.

If a caption contains at least one keyword from KEYWORDS it is
considered a *candidate* event and forwarded to the classifier.
This eliminates general social posts (selfies, shoutouts, etc.)
without spending any GPU time.
"""
from __future__ import annotations

import re

# Extend this list freely — lowercase only, regex supported
KEYWORDS: list[str] = [
    r"\bmeeting\b",
    r"\bjoin us\b",
    r"\btonight\b",
    r"\btomorrow\b",
    r"\bevent\b",
    r"\bworkshop\b",
    r"\bseminar\b",
    r"\binfo session\b",
    r"\bgeneralmeeting\b",
    r"\bgeneral meeting\b",
    r"\bwebinar\b",
    r"\bpanel\b",
    r"\bpresentation\b",
    r"\bhackathon\b",
    r"\btalk\b",
    r"\blecture\b",
    r"\bsocial\b",
    r"\bgame night\b",
    r"\bfilm screening\b",
    r"\bfilm night\b",
    r"\baudit\b",
    r"\bcompetition\b",
    r"\brsvp\b",
    r"\bfree food\b",
    r"\bpizza\b",
    r"\bq&a\b",
    r"\brecruitment\b",
    r"\baudition\b",
    r"\bopen house\b",
    r"\bfair\b",
    r"\bnetworking\b",
    r"\bpotluck\b",
    r"\bfundraiser\b",
    r"\bpublic talk\b",
    r"\bstudy session\b",
    r"\bspring.*\d{4}\b",
    r"\bfall.*\d{4}\b",
    r"\b\d{1,2}[:/]\d{2}\s*(am|pm)\b",  # time patterns like 6:00 PM
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
]

_COMPILED: list[re.Pattern[str]] = [
    re.compile(kw, re.IGNORECASE) for kw in KEYWORDS
]


def is_event_candidate(text: str | None) -> bool:
    """Return True if *text* contains at least one event keyword."""
    if not text:
        return False
    for pattern in _COMPILED:
        if pattern.search(text):
            return True
    return False
