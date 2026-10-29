import os
from collections.abc import AsyncIterator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Serverless (Vercel) freezes/reuses processes between requests, so pooled connections go stale:
# open a fresh connection per request there. Long-running servers keep a normal pool.
_engine_kwargs = {"poolclass": NullPool} if os.getenv("VERCEL") else {"pool_pre_ping": True}
engine = create_async_engine(settings.database_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


# ---- Tenant context for PostgreSQL Row-Level Security ----------------------
# Every transaction on a session that has a tenant gets `app.current_agency` set
# (transaction-local), so RLS policies filter rows even if app code forgets a WHERE.
_SET_TENANT = text("SELECT set_config('app.current_agency', :agency, true)")


@event.listens_for(Session, "after_begin")
def _apply_tenant(session, transaction, connection):
    agency = session.info.get("agency_id")
    if agency and connection.dialect.name == "postgresql":
        connection.execute(_SET_TENANT, {"agency": agency})


async def set_tenant(db: AsyncSession, agency_id) -> None:
    db.info["agency_id"] = str(agency_id)
    if db.bind.dialect.name == "postgresql":
        await db.execute(_SET_TENANT, {"agency": str(agency_id)})
