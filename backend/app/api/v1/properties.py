import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_owned, require_roles
from app.core.db import get_db
from app.models import Property, User
from app.schemas.crm import PropertyCreate, PropertyOut, PropertyUpdate
from app.services.audit import audit
from app.services.matching import run_matching_for_property
from app.services.units import normalize_phone, to_sqft

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("", response_model=PropertyOut, status_code=201)
async def create_property(data: PropertyCreate, user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    prop = Property(**data.model_dump(), agency_id=user.agency_id, created_by=user.id)
    prop.area_sqft = to_sqft(data.area_value, data.area_unit)
    if data.owner_phone:
        prop.owner_phone = normalize_phone(data.owner_phone)
    db.add(prop)
    await db.flush()
    await run_matching_for_property(db, prop)
    await audit(db, user, "create", "property", prop.id)
    await db.commit()
    return prop


@router.get("", response_model=list[PropertyOut])
async def list_properties(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
    q: str | None = None, purpose: str | None = None, status: str | None = None,
    property_type: str | None = None, city: str | None = None, area_name: str | None = None,
    min_price: float | None = None, max_price: float | None = None, bedrooms: int | None = None,
    limit: int = Query(50, le=200), offset: int = 0,
):
    stmt = select(Property).where(Property.agency_id == user.agency_id, Property.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Property.title.ilike(like), Property.area_name.ilike(like), Property.address.ilike(like)))
    for col, val in ((Property.purpose, purpose), (Property.status, status), (Property.property_type, property_type),
                     (Property.city, city), (Property.area_name, area_name), (Property.bedrooms, bedrooms)):
        if val is not None:
            stmt = stmt.where(col == val)
    if min_price is not None:
        stmt = stmt.where(Property.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Property.price <= max_price)
    stmt = stmt.order_by(Property.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


@router.get("/{property_id}", response_model=PropertyOut)
async def get_property(property_id: uuid.UUID, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    return await get_owned(db, Property, property_id, user)


@router.patch("/{property_id}", response_model=PropertyOut)
async def update_property(property_id: uuid.UUID, data: PropertyUpdate, user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    prop = await get_owned(db, Property, property_id, user)
    changes = data.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(prop, k, v)
    prop.area_sqft = to_sqft(prop.area_value, prop.area_unit)
    await db.flush()
    await run_matching_for_property(db, prop)
    await audit(db, user, "update", "property", prop.id, changes)
    await db.commit()
    return prop


@router.delete("/{property_id}", status_code=204)
async def delete_property(property_id: uuid.UUID, user: User = Depends(require_roles("owner", "manager")),
                          db: AsyncSession = Depends(get_db)):
    prop = await get_owned(db, Property, property_id, user)
    prop.deleted_at = datetime.now(timezone.utc)  # soft delete
    await audit(db, user, "delete", "property", prop.id)
    await db.commit()
