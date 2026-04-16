"""
Events router for all /events endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import require_verified_user, get_current_user_optional
from db.database import get_session
from db.models import User
from models.schemas import AttendanceResponse, EventCreateManual, EventRead
from services.events_service import (
    create_manual_event,
    get_event_detail,
    list_all_events,
    list_events_by_club,
    list_today_events,
    list_upcoming_events,
    rsvp_to_event,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead], summary="All events")
async def get_all_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> list[EventRead]:
    return await list_all_events(session, skip=skip, limit=limit, current_user=current_user)


@router.get("/today", response_model=list[EventRead], summary="Events happening today")
async def get_today_events(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> list[EventRead]:
    return await list_today_events(session, current_user=current_user)


@router.get("/upcoming", response_model=list[EventRead], summary="Upcoming events")
async def get_upcoming_events(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> list[EventRead]:
    return await list_upcoming_events(session, current_user=current_user)


@router.get("/club/{club_name}", response_model=list[EventRead], summary="Events by club")
async def get_events_by_club(
    club_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> list[EventRead]:
    return await list_events_by_club(session, club_name=club_name, skip=skip, limit=limit, current_user=current_user)


@router.post(
    "/admin/inject",
    response_model=EventRead,
    status_code=201,
    summary="Inject a featured event (admin only)",
    tags=["admin"],
)
async def inject_event(
    body: EventCreateManual,
    x_admin_key: str = Header(..., description="Admin secret key"),
    session: AsyncSession = Depends(get_session),
) -> EventRead:
    return await create_manual_event(session, body=body, admin_key=x_admin_key)


@router.post(
    "/{event_id}/attendance",
    response_model=AttendanceResponse,
    status_code=200,
    summary="RSVP to an event",
)
async def rsvp_event(
    event_id: int,
    current_user: User = Depends(require_verified_user),
    session: AsyncSession = Depends(get_session),
) -> AttendanceResponse:
    return await rsvp_to_event(session, event_id=event_id, current_user=current_user)


@router.get("/{event_id}", response_model=EventRead, summary="Single event by ID")
async def get_event(
    event_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> EventRead:
    return await get_event_detail(session, event_id, current_user=current_user)
