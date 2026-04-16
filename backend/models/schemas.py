"""
Pydantic v2 schemas used for API responses and internal data transfer.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


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
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool = False
    created_at: datetime
    source_post_permalink: str | None = None
    current_user_going: bool = False
    squad_members_going: list[str] = []


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
    is_public: bool = False


class SquadMemberCreate(BaseModel):
    """
    Join a squad. Provide the user_id of the member to add.
    NOTE: squads.py router must be updated to use this field (was member_name).
    """
    user_id: int


class SquadMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    status: str
    joined_at: datetime
    username: str | None = None

    @model_validator(mode='before')
    @classmethod
    def extract_username(cls, v):
        """
        Pull username out of the eagerly-loaded SquadMember.user relationship
        so the frontend gets a flat { user_id, username } instead of nesting.
        Only runs when v is an ORM instance (has a 'user' attribute).
        """
        if hasattr(v, 'user') and v.user is not None:
            return {
                'id': v.id,
                'user_id': v.user_id,
                'status': v.status,
                'joined_at': v.joined_at,
                'username': v.user.username,
            }
        return v


class SquadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    invite_code: str
    owner_user_id: int | None = None
    is_public: bool
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


# ── Auth (Phase 4+: JWT + email verification) ─────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 30:
            raise ValueError("Username must be 30 characters or fewer")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, hyphens, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.strip().lower()
        parts = v.split("@")
        if len(parts) != 2 or not parts[0] or "." not in parts[1]:
            raise ValueError("Invalid email address")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    email_verified: bool = False
    detail: str | None = None


class UserRead(BaseModel):
    """Full user profile — returned by GET /auth/me."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    email_verified: bool
    auto_invites_enabled: bool
    notify_squad_on_rsvp: bool
    created_at: datetime


class VerifyEmailRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def code_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) != 6 or not v.isdigit():
            raise ValueError("Verification code must be exactly 6 digits")
        return v


class UserSettingsUpdate(BaseModel):
    auto_invites_enabled: bool | None = None
    notify_squad_on_rsvp: bool | None = None


class FollowResponse(BaseModel):
    status: str  # "followed" | "already_following"
    club_username: str
    username: str


class AttendanceResponse(BaseModel):
    event_id: int
    user_id: int
    status: str  # "going" | "already_going"
    notified_squad_count: int = 0
