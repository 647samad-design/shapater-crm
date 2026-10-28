"""Database-level tenant isolation. Runs only against PostgreSQL (as the restricted app role)."""
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.db import engine

pytestmark = pytest.mark.skipif(engine.dialect.name != "postgresql", reason="RLS needs PostgreSQL")

INSERT = text("""INSERT INTO properties (id, agency_id, title, purpose, property_type, status, price, currency,
                 country, features, created_at, updated_at)
                 VALUES (:id, :agency, 'RLS test', 'sale', 'house', 'available', 1, 'PKR', 'PK', '[]', now(), now())""")


async def _agency(conn) -> uuid.UUID:
    aid = uuid.uuid4()
    await conn.execute(text("INSERT INTO agencies (id, name, country, default_currency, plan, created_at, updated_at) "
                            "VALUES (:i, 'rls', 'PK', 'PKR', 'trial', now(), now())"), {"i": aid})
    return aid


async def _as(conn, agency):
    await conn.execute(text("SELECT set_config('app.current_agency', :a, true)"), {"a": str(agency)})


async def test_rows_invisible_across_tenants_and_fail_closed():
    async with engine.begin() as conn:
        a, b = await _agency(conn), await _agency(conn)
        await _as(conn, a)
        await conn.execute(INSERT, {"id": uuid.uuid4(), "agency": a})
    async with engine.begin() as conn:
        await _as(conn, a)
        assert (await conn.execute(text("SELECT count(*) FROM properties"))).scalar_one() >= 1
    async with engine.begin() as conn:
        await _as(conn, b)  # other tenant sees none, even with no WHERE clause
        assert (await conn.execute(text("SELECT count(*) FROM properties WHERE title='RLS test'"))).scalar_one() == 0
    async with engine.begin() as conn:  # no tenant set -> nothing visible (fail-closed)
        assert (await conn.execute(text("SELECT count(*) FROM properties"))).scalar_one() == 0


async def test_cannot_write_into_another_tenant():
    async with engine.begin() as conn:
        a, b = await _agency(conn), await _agency(conn)
    with pytest.raises(DBAPIError):
        async with engine.begin() as conn:
            await _as(conn, a)
            await conn.execute(INSERT, {"id": uuid.uuid4(), "agency": b})  # WITH CHECK must reject
