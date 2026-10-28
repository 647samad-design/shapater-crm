import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_owned
from app.core.db import get_db
from app.models import Client, Match, Property, Requirement, User
from app.schemas.crm import MatchOut, MatchStatusUpdate
from app.services.audit import audit

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchOut])
async def list_matches(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                       requirement_id: uuid.UUID | None = None, property_id: uuid.UUID | None = None,
                       status: str | None = None, min_score: int = 0,
                       limit: int = Query(50, le=200), offset: int = 0):
    stmt = select(Match).where(Match.agency_id == user.agency_id, Match.score >= min_score)
    if requirement_id:
        stmt = stmt.where(Match.requirement_id == requirement_id)
    if property_id:
        stmt = stmt.where(Match.property_id == property_id)
    if status:
        stmt = stmt.where(Match.status == status)
    stmt = stmt.order_by(Match.score.desc(), Match.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


@router.get("/detailed")
async def detailed_matches(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                           status: str | None = None, min_score: int = 0, limit: int = Query(50, le=200),
                           offset: int = 0):
    """Matches joined with property + client summary (one call for the dashboard)."""
    stmt = (select(Match, Property, Requirement, Client)
            .join(Property, Property.id == Match.property_id)
            .join(Requirement, Requirement.id == Match.requirement_id)
            .join(Client, Client.id == Requirement.client_id)
            .where(Match.agency_id == user.agency_id, Match.score >= min_score,
                   Property.deleted_at.is_(None), Client.deleted_at.is_(None)))
    if status:
        stmt = stmt.where(Match.status == status)
    rows = (await db.execute(stmt.order_by(Match.score.desc(), Match.created_at.desc())
                             .limit(limit).offset(offset))).all()
    return [{
        "id": m.id, "score": m.score, "breakdown": m.breakdown, "status": m.status, "created_at": m.created_at,
        "property": {"id": p.id, "title": p.title, "price": float(p.price), "currency": p.currency,
                     "city": p.city, "area_name": p.area_name, "bedrooms": p.bedrooms, "purpose": p.purpose},
        "client": {"id": c.id, "name": c.name, "phone": c.phone},
        "requirement": {"id": r.id, "urgency": r.urgency, "budget_max": float(r.budget_max) if r.budget_max else None,
                        "currency": r.currency, "preferred_areas": r.preferred_areas},
    } for m, p, r, c in rows]


@router.patch("/{match_id}", response_model=MatchOut)
async def update_match(match_id: uuid.UUID, data: MatchStatusUpdate, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    match = await get_owned(db, Match, match_id, user)
    match.status = data.status
    await audit(db, user, "update", "match", match.id, {"status": data.status})
    await db.commit()
    return match


@router.get("/{match_id}/whatsapp")
async def whatsapp_share(match_id: uuid.UUID, user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    """Ready-made WhatsApp message + wa.me click-to-chat link for this match."""
    match = await get_owned(db, Match, match_id, user)
    prop = await get_owned(db, Property, match.property_id, user)
    req = await get_owned(db, Requirement, match.requirement_id, user)
    client = await get_owned(db, Client, req.client_id, user)
    lines = [f"Assalam o Alaikum {client.name},", "", f"🏠 {prop.title}"]
    place = ", ".join(x for x in (prop.area_name, prop.city) if x)
    if place:
        lines.append(f"📍 {place}")
    lines.append(f"💰 {prop.currency} {float(prop.price):,.0f}")
    if prop.bedrooms is not None:
        lines.append(f"🛏 {prop.bedrooms} bedrooms")
    if prop.area_value:
        lines.append(f"📐 {prop.area_value:g} {prop.area_unit}")
    if prop.permit_number:
        lines.append(f"Permit: {prop.permit_number}")
    lines += ["", "Aapki requirement ke mutabiq yeh property fit baithti hai. Viewing arrange kar dun?"]
    text = "\n".join(lines)
    return {"text": text, "wa_link": f"https://wa.me/{client.phone_normalized.lstrip('+')}?text={quote(text)}"}
