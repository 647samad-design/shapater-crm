import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app import models  # noqa: F401
from app.core.config import settings
from app.core.db import Base

config = context.config
target_metadata = Base.metadata
# Migrations run as the DB owner; the app itself runs as a restricted role (RLS applies to it).
URL = settings.migration_database_url or settings.database_url


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async():
    engine = create_async_engine(URL)
    async with engine.connect() as conn:
        await conn.run_sync(run_migrations)
    await engine.dispose()


asyncio.run(run_async())
