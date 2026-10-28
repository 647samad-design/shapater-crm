"""Server-side access to an agency's stored credentials (e.g. Stripe billing, WhatsApp sending)."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt
from app.models import ApiKey


async def get_secret(db: AsyncSession, agency_id: uuid.UUID, provider: str, label: str | None = None) -> str | None:
    stmt = select(ApiKey).where(ApiKey.agency_id == agency_id, ApiKey.provider == provider)
    if label:
        stmt = stmt.where(ApiKey.label == label)
    key = (await db.execute(stmt.order_by(ApiKey.created_at))).scalars().first()
    return decrypt(key.encrypted_value) if key else None
