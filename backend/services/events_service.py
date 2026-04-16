from __future__ import annotations

import logging
import zoneinfo
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.settings import get_settings
from db.models import Event, EventAttendance, SquadMember, User
from models.schemas import AttendanceResponse, EventCreateManual, EventRead
from utils.email_service import send_calendar_invite

logger = logging.getLogger(__name__)

_NY_TZ = zoneinfo.ZoneInfo("America/New_York")


def _event_query():
    return select(Event).options(selectinload(Event.source_post))


async def _get_squad_attendance_map(session: AsyncSession, current_user: User | None, event_ids: list[int]) -> dict[int, list[str]]:
    if not current_user or not event_ids:
        return {}

    query = (
        select(EventAttendance.event_id, User.username)
        .select_from(EventAttendance)
        .join(User, EventAttendance.user_id == User.id)
        .join(SquadMember, SquadMember.user_id == User.id)
        .where(
            EventAttendance.event_id.in_(event_ids),
            SquadMember.squad_id.in_(
                select(SquadMember.squad_id).where(SquadMember.user_id == current_user.id)
            ),
            User.id != current_user.id
        ).distinct()
    )
    result = await session.execute(query)
    mapping = {}
    for ev_id, uname in result:
        mapping.setdefault(ev_id, []).append(uname)
    return mapping


async def _get_current_user_attendance_set(
    session: AsyncSession,
    current_user: User | None,
    event_ids: list[int],
) -> set[int]:
    if not current_user or not event_ids:
        return set()

    result = await session.execute(
        select(EventAttendance.event_id).where(
            EventAttendance.user_id == current_user.id,
            EventAttendance.event_id.in_(event_ids),
        )
    )
    return set(result.scalars().all())


def _serialize_events(
    events: list[Event],
    squad_attendance_map: dict[int, list[str]] | None = None,
    current_user_going_ids: set[int] | None = None,
) -> list[EventRead]:
    serialized = []
    for event in events:
        data = EventRead.model_validate(event)
        if event.source_post:
            data.source_post_permalink = event.source_post.permalink
        if current_user_going_ids and event.id in current_user_going_ids:
            data.current_user_going = True
        if squad_attendance_map and event.id in squad_attendance_map:
            data.squad_members_going = squad_attendance_map[event.id]
        serialized.append(data)
    return serialized


async def list_all_events(session: AsyncSession, skip: int, limit: int, current_user: User | None = None) -> list[EventRead]:
    result = await session.execute(
        _event_query()
        .where(Event.start_at.is_not(None))
        .order_by(Event.start_at.asc(), Event.confidence.desc(), Event.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    events = list(result.scalars().all())
    event_ids = [e.id for e in events]
    atk_map = await _get_squad_attendance_map(session, current_user, event_ids)
    current_user_going_ids = await _get_current_user_attendance_set(session, current_user, event_ids)
    return _serialize_events(events, atk_map, current_user_going_ids)


async def list_today_events(session: AsyncSession, current_user: User | None = None) -> list[EventRead]:
    now_ny = datetime.now(_NY_TZ)
    day_start = now_ny.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    result = await session.execute(
        _event_query()
        .where(
            and_(
                Event.start_at.is_not(None),
                Event.start_at >= day_start,
                Event.start_at < day_end,
            )
        )
        .order_by(Event.start_at.asc().nulls_last(), Event.confidence.desc(), Event.created_at.desc())
    )
    events = list(result.scalars().all())
    event_ids = [e.id for e in events]
    atk_map = await _get_squad_attendance_map(session, current_user, event_ids)
    current_user_going_ids = await _get_current_user_attendance_set(session, current_user, event_ids)
    return _serialize_events(events, atk_map, current_user_going_ids)


async def list_upcoming_events(session: AsyncSession, current_user: User | None = None) -> list[EventRead]:
    now_ny = datetime.now(_NY_TZ)
    result = await session.execute(
        _event_query()
        .where(and_(Event.start_at.is_not(None), Event.start_at >= now_ny))
        .order_by(Event.start_at.asc().nulls_last(), Event.confidence.desc(), Event.created_at.desc())
        .limit(100)
    )
    events = list(result.scalars().all())
    event_ids = [e.id for e in events]
    atk_map = await _get_squad_attendance_map(session, current_user, event_ids)
    current_user_going_ids = await _get_current_user_attendance_set(session, current_user, event_ids)
    return _serialize_events(events, atk_map, current_user_going_ids)


async def list_events_by_club(
    session: AsyncSession,
    club_name: str,
    skip: int,
    limit: int,
    current_user: User | None = None,
) -> list[EventRead]:
    result = await session.execute(
        _event_query()
        .where(func.lower(Event.club) == club_name.lower())
        .order_by(Event.confidence.desc(), Event.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    events = list(result.scalars().all())
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for club '{club_name}'")
        
    event_ids = [e.id for e in events]
    atk_map = await _get_squad_attendance_map(session, current_user, event_ids)
    current_user_going_ids = await _get_current_user_attendance_set(session, current_user, event_ids)
    return _serialize_events(events, atk_map, current_user_going_ids)


async def get_event_detail(session: AsyncSession, event_id: int, current_user: User | None = None) -> EventRead:
    result = await session.execute(
        _event_query().where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
        
    atk_map = await _get_squad_attendance_map(session, current_user, [event.id])
    current_user_going_ids = await _get_current_user_attendance_set(session, current_user, [event.id])
    return _serialize_events([event], atk_map, current_user_going_ids)[0]


async def create_manual_event(
    session: AsyncSession,
    body: EventCreateManual,
    admin_key: str,
) -> EventRead:
    settings = get_settings()
    if not settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail="Admin injection is disabled (ADMIN_SECRET_KEY not configured).",
        )

    if admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key.")

    event = Event(
        club=body.club.strip(),
        rso_name=body.rso_name.strip() if body.rso_name else None,
        title=body.title.strip(),
        date=body.date,
        time=body.time,
        location=body.location,
        description=body.description,
        confidence=1.0,
        source_post_id=None,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)

    logger.info("Admin injected event id=%d: %r", event.id, event.title)
    return _serialize_events([event])[0]


async def rsvp_to_event(
    session: AsyncSession,
    event_id: int,
    current_user: User,
) -> AttendanceResponse:
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    existing = await session.execute(
        select(EventAttendance).where(
            EventAttendance.user_id == current_user.id,
            EventAttendance.event_id == event_id,
        )
    )
    status = "already_going"
    notified_count = 0

    if existing.scalar_one_or_none() is None:
        attendance = EventAttendance(
            user_id=current_user.id,
            event_id=event_id,
            notify_squads=current_user.notify_squad_on_rsvp,
        )
        session.add(attendance)
        await session.commit()
        status = "going"
        logger.info(
            "User %s (id=%d) RSVPed to event id=%d: %r",
            current_user.username, current_user.id, event_id, event.title,
        )

        if current_user.email and current_user.email_verified:
            send_calendar_invite(current_user.email, event)

        if current_user.notify_squad_on_rsvp:
            squad_ids_result = await session.execute(
                select(SquadMember.squad_id).where(SquadMember.user_id == current_user.id)
            )
            squad_ids = list(squad_ids_result.scalars().all())

            if squad_ids:
                mate_ids_result = await session.execute(
                    select(SquadMember.user_id)
                    .where(
                        SquadMember.squad_id.in_(squad_ids),
                        SquadMember.user_id != current_user.id,
                        SquadMember.user_id.is_not(None),
                    )
                    .distinct()
                )
                mate_ids = list(mate_ids_result.scalars().all())

                if mate_ids:
                    mates_result = await session.execute(
                        select(User).where(
                            User.id.in_(mate_ids),
                            User.email.is_not(None),
                        )
                    )
                    for mate in mates_result.scalars().all():
                        send_calendar_invite(
                            user_email=mate.email,
                            event=event,
                            message_body=f"Your squad-mate @{current_user.username} is going to {event.title}.",
                        )
                        notified_count += 1

    return AttendanceResponse(
        event_id=event_id,
        user_id=current_user.id,
        status=status,
        notified_squad_count=notified_count,
    )
