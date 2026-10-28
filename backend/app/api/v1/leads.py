import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_owned
from app.core.db import get_db
from app.models import Activity, Client, Lead, User
from app.schemas.crm import ActivityCreate, ActivityOut, LeadCreate, LeadOut, LeadUpdate
from app.services.audit import audit

router = APIRouter(tags=["leads"])


@router.post("/leads", response_model=LeadOut, status_code=201)
async def create_lead(data: LeadCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await get_owned(db, Client, data.client_id, user)
    fields = data.model_dump()
    fields["assigned_to"] = data.assigned_to or user.id
    lead = Lead(**fields, agency_id=user.agency_id)
    db.add(lead)
    await db.flush()
    await audit(db, user, "create", "lead", lead.id)
    await db.commit()
    return lead


@router.get("/leads", response_model=list[LeadOut])
async def list_leads(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                     stage: str | None = None, assigned_to: uuid.UUID | None = None, source: str | None = None,
                     limit: int = Query(100, le=500), offset: int = 0):
    stmt = select(Lead).where(Lead.agency_id == user.agency_id)
    if stage:
        stmt = stmt.where(Lead.stage == stage)
    if assigned_to:
        stmt = stmt.where(Lead.assigned_to == assigned_to)
    if source:
        stmt = stmt.where(Lead.source == source)
    stmt = stmt.order_by(Lead.updated_at.desc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


@router.patch("/leads/{lead_id}", response_model=LeadOut)
async def update_lead(lead_id: uuid.UUID, data: LeadUpdate, user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    lead = await get_owned(db, Lead, lead_id, user)
    changes = data.model_dump(exclude_unset=True)
    old_stage = lead.stage
    for k, v in changes.items():
        setattr(lead, k, v)
    await audit(db, user, "update", "lead", lead.id, {k: str(v) for k, v in changes.items()} | {"old_stage": old_stage})
    await db.commit()
    return lead


@router.post("/leads/{lead_id}/activities", response_model=ActivityOut, status_code=201)
async def add_activity(lead_id: uuid.UUID, data: ActivityCreate, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    lead = await get_owned(db, Lead, lead_id, user)
    act = Activity(**data.model_dump(), agency_id=user.agency_id, lead_id=lead.id,
                   client_id=lead.client_id, user_id=user.id)
    db.add(act)
    await db.commit()
    return act


@router.get("/leads/{lead_id}/activities", response_model=list[ActivityOut])
async def lead_activities(lead_id: uuid.UUID, user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    await get_owned(db, Lead, lead_id, user)
    rows = await db.execute(select(Activity).where(Activity.agency_id == user.agency_id, Activity.lead_id == lead_id)
                            .order_by(Activity.created_at.desc()))
    return rows.scalars().all()


@router.get("/activities/due", response_model=list[ActivityOut])
async def due_followups(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Pending follow-ups that are due now or overdue, for the logged-in user."""
    rows = await db.execute(select(Activity).where(
        Activity.agency_id == user.agency_id, Activity.user_id == user.id, Activity.done.is_(False),
        Activity.due_at.is_not(None), Activity.due_at <= datetime.now(timezone.utc)).order_by(Activity.due_at))
    return rows.scalars().all()


@router.post("/activities/{activity_id}/done", response_model=ActivityOut)
async def complete_activity(activity_id: uuid.UUID, user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    act = await get_owned(db, Activity, activity_id, user)
    act.done = True
    await db.commit()
    return act
