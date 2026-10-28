import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_owned
from app.core.db import get_db
from app.models import Client, Requirement, User
from app.schemas.crm import RequirementCreate, RequirementOut, RequirementUpdate
from app.services.audit import audit
from app.services.matching import run_matching_for_requirement

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.post("", response_model=RequirementOut, status_code=201)
async def create_requirement(data: RequirementCreate, user: User = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    await get_owned(db, Client, data.client_id, user)  # client must belong to this agency
    req = Requirement(**data.model_dump(), agency_id=user.agency_id)
    db.add(req)
    await db.flush()
    await run_matching_for_requirement(db, req)  # auto-match instantly
    await audit(db, user, "create", "requirement", req.id)
    await db.commit()
    return req


@router.get("", response_model=list[RequirementOut])
async def list_requirements(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                            client_id: uuid.UUID | None = None, active: bool | None = None,
                            limit: int = Query(50, le=200), offset: int = 0):
    stmt = select(Requirement).where(Requirement.agency_id == user.agency_id)
    if client_id:
        stmt = stmt.where(Requirement.client_id == client_id)
    if active is not None:
        stmt = stmt.where(Requirement.is_active.is_(active))
    stmt = stmt.order_by(Requirement.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


@router.patch("/{requirement_id}", response_model=RequirementOut)
async def update_requirement(requirement_id: uuid.UUID, data: RequirementUpdate,
                             user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    req = await get_owned(db, Requirement, requirement_id, user)
    changes = data.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(req, k, v)
    await db.flush()
    if req.is_active:
        await run_matching_for_requirement(db, req)
    await audit(db, user, "update", "requirement", req.id, {k: str(v) for k, v in changes.items()})
    await db.commit()
    return req
