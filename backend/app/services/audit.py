import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User


async def audit(db: AsyncSession, user: User, action: str, entity: str,
                entity_id: uuid.UUID | None = None, changes: dict | None = None) -> None:
    db.add(AuditLog(agency_id=user.agency_id, user_id=user.id, action=action,
                    entity=entity, entity_id=entity_id, changes=changes or {}))
