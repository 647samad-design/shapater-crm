from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models import Client, Lead, Match, Property, Requirement, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    a = user.agency_id

    async def count(stmt):
        return (await db.execute(stmt)).scalar_one()

    stages = (await db.execute(select(Lead.stage, func.count()).where(Lead.agency_id == a).group_by(Lead.stage))).all()
    sources = (await db.execute(select(func.coalesce(Lead.source, "unknown"), func.count())
                                .where(Lead.agency_id == a).group_by(Lead.source))).all()
    total_leads = sum(c for _, c in stages)
    won = dict(stages).get("won", 0)
    return {
        "properties_available": await count(select(func.count()).select_from(Property).where(
            Property.agency_id == a, Property.deleted_at.is_(None), Property.status == "available")),
        "clients": await count(select(func.count()).select_from(Client).where(
            Client.agency_id == a, Client.deleted_at.is_(None))),
        "active_requirements": await count(select(func.count()).select_from(Requirement).where(
            Requirement.agency_id == a, Requirement.is_active.is_(True))),
        "new_matches": await count(select(func.count()).select_from(Match).where(
            Match.agency_id == a, Match.status == "new")),
        "leads_by_stage": {s: c for s, c in stages},
        "leads_by_source": {s: c for s, c in sources},
        "conversion_rate": round(won / total_leads * 100, 1) if total_leads else 0.0,
    }
