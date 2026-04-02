"""
Events router — all /events endpoints.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Event
from models.schemas import EventRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead], summary="All events")
async def get_all_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[Event]:
    """
    Return all events ordered by creation date (newest first).
    Supports pagination via `skip` and `limit`.
    """
    result = await session.execute(
        select(Event)
        .order_by(Event.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/today", response_model=list[EventRead], summary="Events happening today")
async def get_today_events(
    session: AsyncSession = Depends(get_session),
) -> list[Event]:
    """
    Return events whose `date` field contains today's date string.
    The date field is free-text from the LLM, so we use a LIKE match
    on both the ISO date and common month/day formats.
    """
    today = date.today()
    today_str = today.strftime("%-m/%-d")           # e.g. "3/14"
    today_str_long = today.strftime("%B %-d")        # e.g. "March 14"
    today_iso = today.isoformat()                    # e.g. "2025-03-14"
    today_day = today.strftime("%A")                 # e.g. "Friday"

    result = await session.execute(
        select(Event).where(
            Event.date.ilike(f"%{today_str}%")
            | Event.date.ilike(f"%{today_str_long}%")
            | Event.date.ilike(f"%{today_iso}%")
            | Event.date.ilike(f"%{today_day}%")
        ).order_by(Event.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/upcoming", response_model=list[EventRead], summary="Events created in the last 14 days")
async def get_upcoming_events(
    days: int = Query(14, ge=1, le=90, description="Look-back window in days"),
    session: AsyncSession = Depends(get_session),
) -> list[Event]:
    """
    Return events created within the last *days* days.
    Because dates are stored as free-text we proxy 'upcoming' by
    creation time — events scraped recently are almost always upcoming.
    """
    from datetime import timedelta

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    result = await session.execute(
        select(Event)
        .where(Event.created_at >= cutoff)
        .order_by(Event.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


@router.get("/club/{club_name}", response_model=list[EventRead], summary="Events by club")
async def get_events_by_club(
    club_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[Event]:
    """Return all events belonging to *club_name* (case-insensitive)."""
    result = await session.execute(
        select(Event)
        .where(func.lower(Event.club) == club_name.lower())
        .order_by(Event.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    events = list(result.scalars().all())
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for club '{club_name}'")
    return events


@router.get("/{event_id}", response_model=EventRead, summary="Single event by ID")
async def get_event(
    event_id: int,
    session: AsyncSession = Depends(get_session),
) -> Event:
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
