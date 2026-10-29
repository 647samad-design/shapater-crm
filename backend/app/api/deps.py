import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, set_tenant
from app.core.security import decode_token
from app.models import User

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2), db: AsyncSession = Depends(get_db)) -> User:
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    try:
        payload = decode_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise err
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user or not user.is_active:
        raise err
    await set_tenant(db, user.agency_id)  # activates RLS for the rest of this request
    return user


def require_roles(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user
    return checker


def is_agent(user: User) -> bool:
    return user.role == "agent"


def visible_client_ids(user: User):
    """Sub-select of client ids an agent may see (owners/managers see the whole agency)."""
    from app.models import Client
    return select(Client.id).where(Client.agency_id == user.agency_id, Client.assigned_to == user.id)


async def get_client_for(db: AsyncSession, client_id: uuid.UUID, user: User):
    from app.models import Client
    c = await get_owned(db, Client, client_id, user)
    if is_agent(user) and c.assigned_to != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")
    return c


async def get_requirement_for(db: AsyncSession, req_id: uuid.UUID, user: User):
    from app.models import Requirement
    r = await get_owned(db, Requirement, req_id, user)
    await get_client_for(db, r.client_id, user)
    return r


async def get_lead_for(db: AsyncSession, lead_id: uuid.UUID, user: User):
    from app.models import Lead
    lead = await get_owned(db, Lead, lead_id, user)
    if is_agent(user) and lead.assigned_to != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    return lead


async def get_owned(db: AsyncSession, model, obj_id: uuid.UUID, user: User):
    """Fetch an object scoped to the caller's agency (tenant isolation) or 404."""
    stmt = select(model).where(model.id == obj_id, model.agency_id == user.agency_id)
    if hasattr(model, "deleted_at"):
        stmt = stmt.where(model.deleted_at.is_(None))
    obj = (await db.execute(stmt)).scalar_one_or_none()
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} not found")
    return obj
