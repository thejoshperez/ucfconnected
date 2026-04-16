"""
Squads router for create, view, and join flows.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user, require_verified_user
from db.database import get_session
from db.models import Squad, User
from models.schemas import SquadCreate, SquadResponse
from services.squads_service import (
    approve_member,
    create_squad as create_squad_service,
    delete_squad as delete_squad_service,
    get_squad_by_code,
    join_squad as join_squad_service,
    list_public_squads,
    list_user_squads,
)

router = APIRouter(prefix="/squads", tags=["squads"])


@router.post("", response_model=SquadResponse, status_code=201, summary="Create a squad")
async def create_squad(
    body: SquadCreate,
    current_user: User = Depends(require_verified_user),
    session: AsyncSession = Depends(get_session),
) -> Squad:
    return await create_squad_service(session, body=body, current_user=current_user)


@router.get("", response_model=list[SquadResponse], summary="List public squads")
async def get_public_squads(
    session: AsyncSession = Depends(get_session),
) -> list[Squad]:
    return await list_public_squads(session)


@router.get("/mine", response_model=list[SquadResponse], summary="List my squads")
async def get_my_squads(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Squad]:
    return await list_user_squads(session, current_user=current_user)


@router.get(
    "/{invite_code}",
    response_model=SquadResponse,
    summary="Get squad details by invite code",
)
async def get_squad(
    invite_code: str,
    session: AsyncSession = Depends(get_session),
) -> Squad:
    return await get_squad_by_code(invite_code, session)


@router.post(
    "/{invite_code}/join",
    response_model=SquadResponse,
    status_code=200,
    summary="Join a squad",
)
async def join_squad(
    invite_code: str,
    current_user: User = Depends(require_verified_user),
    session: AsyncSession = Depends(get_session),
) -> Squad:
    return await join_squad_service(session, invite_code=invite_code, current_user=current_user)


@router.post(
    "/{invite_code}/members/{user_id}/approve",
    response_model=SquadResponse,
    summary="Approve a pending member",
)
async def approve_squad_member(
    invite_code: str,
    user_id: int,
    current_user: User = Depends(require_verified_user),
    session: AsyncSession = Depends(get_session),
) -> Squad:
    return await approve_member(
        session,
        invite_code=invite_code,
        user_id=user_id,
        current_user=current_user,
    )


@router.delete(
    "/{invite_code}",
    status_code=204,
    summary="Delete a squad",
    response_class=Response,
)
async def delete_squad(
    invite_code: str,
    current_user: User = Depends(require_verified_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await delete_squad_service(session, invite_code=invite_code, current_user=current_user)
    return Response(status_code=204)
