"""
Pydantic v2 schemas used for API responses and internal data transfer.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PostBase(BaseModel):
    club_username: str
    caption: str | None = None
    timestamp: datetime | None = None
    image_url: str | None = None
    permalink: str | None = None


class PostRead(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    processed: bool
    created_at: datetime


class EventBase(BaseModel):
    club: str
    rso_name: str | None = None
    title: str
    date: str | None = None
    time: str | None = None
    location: str | None = None
    description: str | None = None
    confidence: float = 0.0
    source_post_id: int | None = None


class EventRead(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    source_post_permalink: str | None = None


class ExtractedEventPayload(BaseModel):
    """Shape returned by the LLM extractor."""
    title: str = ""
    date: str = ""
    time: str = ""
    location: str = ""
    description: str = ""


class GeminiExtractedEvent(BaseModel):
    """
    Structured output schema enforced on every Gemini extraction call.
    Passed directly as response_schema= to the Gemini API.
    """
    event_name: str
    rso_name: str
    location: str
    start_time: str  # ISO 8601 preferred ("2025-03-21T18:00:00"), normalized string fallback
    is_valid_event: bool

class ClassifierResult(BaseModel):
    post_id: int
    is_event: bool
    confidence: float


class QueuedPost(BaseModel):
    """Lightweight message placed on the Redis queue."""
    post_id: int
    club_username: str
    caption: str | None = None
    image_url: str | None = None
    permalink: str | None = None


# ── Squad (Phase 3: Viral Mechanics) ─────────────────────────────────────────

class SquadCreate(BaseModel):
    name: str


class SquadMemberCreate(BaseModel):
    member_name: str


class SquadMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_name: str
    joined_at: datetime


class SquadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    invite_code: str
    created_at: datetime
    members: list[SquadMemberRead] = []


class EventCreateManual(BaseModel):
    """Payload for the admin manual-inject endpoint."""
    title: str
    club: str
    rso_name: str | None = None
    date: str | None = None
    time: str | None = None
    location: str | None = None
    description: str | None = None
    image_url: str | None = None
