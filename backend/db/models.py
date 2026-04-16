"""
SQLAlchemy ORM models.

Schema
------
posts              — raw scraped Instagram posts
events             — structured events extracted from posts
squads             — friend groups for sharing events
squad_members      — user membership in a squad
users              — registered accounts
follows            — user → club follow relationships
event_attendance   — user RSVP/attendance for an event
email_delivery_log — deduplication log for email invites
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club_username: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    permalink: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    event: Mapped[Event | None] = relationship("Event", back_populates="source_post", uselist=False)

    def __repr__(self) -> str:
        return f"<Post id={self.id} club={self.club_username!r}>"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    rso_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    date: Mapped[str | None] = mapped_column(String(60), nullable=True)   # human-readable
    time: Mapped[str | None] = mapped_column(String(60), nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source_post_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # ── Structured time fields (v2) ───────────────────────────────────────
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source_post: Mapped[Post | None] = relationship("Post", back_populates="event")
    attendances: Mapped[list[EventAttendance]] = relationship(
        "EventAttendance", back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} title={self.title!r} club={self.club!r}>"


class Squad(Base):
    __tablename__ = "squads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(6), unique=True, index=True, nullable=False)
    # ── Owner (v2) ────────────────────────────────────────────────────────
    owner_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped[User | None] = relationship("User", back_populates="owned_squads")
    members: Mapped[list[SquadMember]] = relationship(
        "SquadMember", back_populates="squad", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Squad id={self.id} name={self.name!r} code={self.invite_code!r}>"


class SquadMember(Base):
    __tablename__ = "squad_members"

    __table_args__ = (
        UniqueConstraint("squad_id", "user_id", name="uq_squad_member_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    squad_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("squads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # member_name replaced by user_id in v2.
    # The DB column member_name still exists as an orphan for migration safety.
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="approved", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    squad: Mapped[Squad] = relationship("Squad", back_populates="members")
    user: Mapped[User | None] = relationship("User", back_populates="squad_memberships")

    def __repr__(self) -> str:
        return f"<SquadMember id={self.id} user_id={self.user_id} squad_id={self.squad_id}>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(72), nullable=False)
    # ── Email verification (v2) ───────────────────────────────────────────
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    # ── Notification preferences (v2) ─────────────────────────────────────
    auto_invites_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_squad_on_rsvp: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    follows: Mapped[list[Follow]] = relationship(
        "Follow", back_populates="user", cascade="all, delete-orphan"
    )
    owned_squads: Mapped[list[Squad]] = relationship(
        "Squad", back_populates="owner"
    )
    squad_memberships: Mapped[list[SquadMember]] = relationship(
        "SquadMember", back_populates="user", cascade="all, delete-orphan"
    )
    event_attendances: Mapped[list[EventAttendance]] = relationship(
        "EventAttendance", back_populates="user", cascade="all, delete-orphan"
    )
    email_delivery_logs: Mapped[list[EmailDeliveryLog]] = relationship(
        "EmailDeliveryLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


class Follow(Base):
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    club_username: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="follows")

    def __repr__(self) -> str:
        return f"<Follow id={self.id} user_id={self.user_id} club={self.club_username!r}>"


class EventAttendance(Base):
    __tablename__ = "event_attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notify_squads: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="event_attendances")
    event: Mapped[Event] = relationship("Event", back_populates="attendances")

    def __repr__(self) -> str:
        return f"<EventAttendance id={self.id} user_id={self.user_id} event_id={self.event_id}>"


class EmailDeliveryLog(Base):
    __tablename__ = "email_delivery_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. 'calendar_invite', 'verification'
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="email_delivery_logs")

    def __repr__(self) -> str:
        return f"<EmailDeliveryLog id={self.id} user_id={self.user_id} type={self.type!r}>"
