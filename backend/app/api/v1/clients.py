import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_owned, require_roles
from app.core.db import get_db
from app.models import Client, User
from app.schemas.crm import ClientCreate, ClientOut, ClientUpdate
from app.services.audit import audit
from app.services.units import normalize_phone

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientOut, status_code=201)
async def create_client(data: ClientCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    phone_n = normalize_phone(data.phone)
    dup = (await db.execute(select(Client).where(
        Client.agency_id == user.agency_id, Client.phone_normalized == phone_n))).scalar_one_or_none()
    if dup and dup.deleted_at is None:  # duplicate detection: same phone already exists in this agency
        raise HTTPException(status.HTTP_409_CONFLICT,
                            detail={"message": "Client with this phone already exists", "client_id": str(dup.id)})
    if dup:  # previously soft-deleted -> restore with fresh details
        for k, v in data.model_dump().items():
            setattr(dup, k, v)
        dup.deleted_at = None
        await audit(db, user, "restore", "client", dup.id)
        await db.commit()
        return dup
    client = Client(**data.model_dump(), agency_id=user.agency_id, phone_normalized=phone_n)
    db.add(client)
    await db.flush()
    await audit(db, user, "create", "client", client.id)
    await db.commit()
    return client


@router.get("", response_model=list[ClientOut])
async def list_clients(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
                       q: str | None = None, source: str | None = None,
                       limit: int = Query(50, le=200), offset: int = 0):
    stmt = select(Client).where(Client.agency_id == user.agency_id, Client.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Client.name.ilike(like), Client.phone.ilike(like), Client.phone_normalized.ilike(like)))
    if source:
        stmt = stmt.where(Client.source == source)
    stmt = stmt.order_by(Client.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(stmt)).scalars().all()


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(client_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_owned(db, Client, client_id, user)


@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(client_id: uuid.UUID, data: ClientUpdate, user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    client = await get_owned(db, Client, client_id, user)
    changes = data.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(client, k, v)
    await audit(db, user, "update", "client", client.id, {k: str(v) for k, v in changes.items()})
    await db.commit()
    return client


@router.delete("/{client_id}", status_code=204)
async def delete_client(client_id: uuid.UUID, user: User = Depends(require_roles("owner", "manager")),
                        db: AsyncSession = Depends(get_db)):
    client = await get_owned(db, Client, client_id, user)
    client.deleted_at = datetime.now(timezone.utc)
    await audit(db, user, "delete", "client", client.id)
    await db.commit()
