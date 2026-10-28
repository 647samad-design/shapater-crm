import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")  # set to a Postgres URL to test RLS
os.environ["SECRET_KEY"] = "test-secret"

import httpx  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.core.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _db():
    if engine.dialect.name == "sqlite":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    else:  # Postgres: schema comes from Alembic; wipe data using the admin URL
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        admin = create_async_engine(os.environ["TEST_ADMIN_DATABASE_URL"])
        async with admin.begin() as conn:
            await conn.execute(text("TRUNCATE audit_logs, api_keys, activities, leads, matches, requirements, clients, "
                                    "properties, users, agencies CASCADE"))
        await admin.dispose()
    yield
    await engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def register(client, email: str, agency: str = "Test Estate"):
    r = await client.post("/api/v1/auth/register", json={
        "agency_name": agency, "full_name": "Owner", "email": email, "password": "supersecret1"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
