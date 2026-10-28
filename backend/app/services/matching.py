"""Property <-> Requirement matching.

score_match() is a pure function (no DB) so it is easy to test and to swap
for an embeddings/AI ranker later. Result is explainable via `breakdown`.
"""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Match, Property, Requirement
from app.services.units import to_usd

WEIGHTS = {"budget": 30, "location": 25, "type": 15, "bedrooms": 15, "features": 15}


def _lower(items) -> set[str]:
    return {str(i).strip().lower() for i in (items or [])}


def _budget(req: Any, prop: Any) -> tuple[float, str]:
    w = WEIGHTS["budget"]
    if req.budget_min is None and req.budget_max is None:
        return w, "no budget set"
    price = to_usd(prop.price, prop.currency)
    lo = to_usd(req.budget_min, req.currency) if req.budget_min is not None else None
    hi = to_usd(req.budget_max, req.currency) if req.budget_max is not None else None
    if hi is not None and price > hi:
        over = (price - hi) / hi * 100
        if over <= 10:
            return w * 0.65, f"{over:.0f}% over budget"
        if over <= 20:
            return w * 0.3, f"{over:.0f}% over budget"
        return 0, f"{over:.0f}% over budget"
    if lo is not None and price < lo:
        return w * 0.8, "below min budget"
    return w, "within budget"


def _location(req: Any, prop: Any) -> tuple[float, str]:
    w = WEIGHTS["location"]
    areas = _lower(req.preferred_areas)
    city_ok = not req.city or (prop.city or "").strip().lower() == req.city.strip().lower()
    if not areas:
        return (w, "no area preference") if city_ok else (0, "different city")
    if (prop.area_name or "").strip().lower() in areas:
        return (w, "preferred area") if city_ok else (w * 0.4, "area matches, city differs")
    return (w * 0.4, "same city, other area") if city_ok and req.city else (0, "area not preferred")


def _type(req: Any, prop: Any) -> tuple[float, str]:
    types = _lower(req.property_types)
    if not types:
        return WEIGHTS["type"], "any type"
    return (WEIGHTS["type"], "type matches") if prop.property_type.lower() in types else (0, "type differs")


def _bedrooms(req: Any, prop: Any) -> tuple[float, str]:
    w = WEIGHTS["bedrooms"]
    if req.bedrooms_min is None and req.bedrooms_max is None:
        return w, "any bedrooms"
    if prop.bedrooms is None:
        return w * 0.3, "bedrooms unknown"
    lo = req.bedrooms_min if req.bedrooms_min is not None else 0
    hi = req.bedrooms_max if req.bedrooms_max is not None else 99
    if lo <= prop.bedrooms <= hi:
        return w, "bedrooms fit"
    diff = lo - prop.bedrooms if prop.bedrooms < lo else prop.bedrooms - hi
    return (w * 0.55, f"{diff} bedroom off") if diff == 1 else (0, f"{diff} bedrooms off")


def _features(req: Any, prop: Any) -> tuple[float, str]:
    needed = _lower(req.required_features)
    if not needed:
        return WEIGHTS["features"], "no extras required"
    have = _lower(prop.features)
    hit = len(needed & have)
    missing = sorted(needed - have)
    note = "all extras present" if not missing else "missing: " + ", ".join(missing)
    return WEIGHTS["features"] * hit / len(needed), note


def score_match(req: Any, prop: Any) -> dict | None:
    """Return {'score': int, 'breakdown': {...}} or None if a hard filter fails."""
    if req.purpose != prop.purpose or prop.status != "available":
        return None
    parts = {
        "budget": _budget(req, prop),
        "location": _location(req, prop),
        "type": _type(req, prop),
        "bedrooms": _bedrooms(req, prop),
        "features": _features(req, prop),
    }
    total = round(sum(p[0] for p in parts.values()))
    return {
        "score": total,
        "breakdown": {k: {"points": round(v[0], 1), "max": WEIGHTS[k], "note": v[1]} for k, v in parts.items()},
    }


async def _upsert(db: AsyncSession, agency_id, req: Requirement, prop: Property, result: dict) -> bool:
    """Create or refresh a Match. Returns True if newly created."""
    existing = (
        await db.execute(select(Match).where(Match.requirement_id == req.id, Match.property_id == prop.id))
    ).scalar_one_or_none()
    if existing:
        existing.score, existing.breakdown = result["score"], result["breakdown"]
        return False
    db.add(Match(agency_id=agency_id, requirement_id=req.id, property_id=prop.id,
                 score=result["score"], breakdown=result["breakdown"]))
    return True


async def run_matching_for_property(db: AsyncSession, prop: Property) -> int:
    reqs = (await db.execute(select(Requirement).where(
        Requirement.agency_id == prop.agency_id, Requirement.is_active.is_(True),
        Requirement.purpose == prop.purpose))).scalars().all()
    created = 0
    for req in reqs:
        res = score_match(req, prop)
        if res and res["score"] >= settings.match_threshold:
            created += await _upsert(db, prop.agency_id, req, prop, res)
    return created


async def run_matching_for_requirement(db: AsyncSession, req: Requirement) -> int:
    props = (await db.execute(select(Property).where(
        Property.agency_id == req.agency_id, Property.deleted_at.is_(None),
        Property.status == "available", Property.purpose == req.purpose))).scalars().all()
    created = 0
    for prop in props:
        res = score_match(req, prop)
        if res and res["score"] >= settings.match_threshold:
            created += await _upsert(db, req.agency_id, req, prop, res)
    return created
