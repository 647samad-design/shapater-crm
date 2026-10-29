"""CSV import (agents' data lives in Excel/WhatsApp exports) + WhatsApp message parsing."""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, is_agent
from app.core.db import get_db
from app.models import Agency, Client, Property, User
from app.schemas.crm import PropertyCreate
from app.services.audit import audit
from app.services.matching import run_matching_for_property
from app.services.parser import parse_message
from app.services.units import normalize_phone, to_sqft

router = APIRouter(tags=["import"])
MAX_ROWS = 5000

CLIENT_ALIASES = {"name": ("name", "client", "client name", "customer"),
                  "phone": ("phone", "mobile", "contact", "number", "whatsapp", "cell"),
                  "email": ("email", "e-mail"), "source": ("source", "lead source"), "notes": ("notes", "note", "remarks")}
PROP_ALIASES = {"title": ("title", "name", "property"), "purpose": ("purpose", "for"),
                "property_type": ("type", "property type", "property_type"), "price": ("price", "demand", "amount"),
                "currency": ("currency", "ccy"), "bedrooms": ("bedrooms", "beds", "bed"),
                "bathrooms": ("bathrooms", "baths"), "city": ("city",), "area_name": ("area", "location", "society", "locality"),
                "area_value": ("size", "area size", "area_value"), "area_unit": ("unit", "size unit", "area_unit"),
                "owner_name": ("owner", "owner name"), "owner_phone": ("owner phone", "owner contact", "owner_phone"),
                "permit_number": ("permit", "permit number", "trakheesi", "rera")}


async def _read_csv(file: UploadFile) -> list[dict]:
    raw = (await file.read()).decode("utf-8-sig", errors="replace")
    rows = list(csv.DictReader(io.StringIO(raw)))
    if len(rows) > MAX_ROWS:
        raise HTTPException(413, f"Max {MAX_ROWS} rows per import")
    return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in rows]


def _map(row: dict, aliases: dict) -> dict:
    out = {}
    for field, names in aliases.items():
        for n in names:
            if row.get(n):
                out[field] = row[n]
                break
    return out


@router.post("/import/clients")
async def import_clients(file: UploadFile, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    created, duplicates, errors = 0, 0, []
    seen: set[str] = set()
    for i, row in enumerate(await _read_csv(file), start=2):
        d = _map(row, CLIENT_ALIASES)
        if not d.get("name") or not d.get("phone"):
            errors.append({"row": i, "error": "name and phone are required"})
            continue
        phone_n = normalize_phone(d["phone"])
        exists = (await db.execute(select(Client.id).where(
            Client.agency_id == user.agency_id, Client.phone_normalized == phone_n))).first()
        if exists or phone_n in seen:
            duplicates += 1
            continue
        seen.add(phone_n)
        db.add(Client(agency_id=user.agency_id, phone_normalized=phone_n, assigned_to=user.id, **d))
        created += 1
    await audit(db, user, "import", "client", None, {"created": created, "duplicates": duplicates})
    await db.commit()
    return {"created": created, "duplicates_skipped": duplicates, "errors": errors}


@router.post("/import/properties")
async def import_properties(file: UploadFile, user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    agency = (await db.execute(select(Agency).where(Agency.id == user.agency_id))).scalar_one()
    created, errors = 0, []
    for i, row in enumerate(await _read_csv(file), start=2):
        d = _map(row, PROP_ALIASES)
        try:
            d.setdefault("currency", agency.default_currency)
            d["purpose"] = d.get("purpose", "sale").lower()
            d["purpose"] = "rent" if d["purpose"].startswith("rent") else "sale"
            d["price"] = float(d.get("price", "").replace(",", ""))
            for k in ("bedrooms", "bathrooms"):
                if k in d:
                    d[k] = int(float(d[k]))
            if "area_value" in d:
                d["area_value"] = float(d["area_value"])
            d.setdefault("property_type", "house")
            d.setdefault("title", f"{d['property_type'].title()} {d.get('area_name', '')}".strip())
            data = PropertyCreate(**d)
        except (ValueError, ValidationError, TypeError) as e:
            errors.append({"row": i, "error": str(e).splitlines()[0][:150]})
            continue
        prop = Property(**data.model_dump(), agency_id=user.agency_id, created_by=user.id)
        prop.area_sqft = to_sqft(data.area_value, data.area_unit)
        if data.owner_phone:
            prop.owner_phone = normalize_phone(data.owner_phone)
        db.add(prop)
        await db.flush()
        await run_matching_for_property(db, prop)
        created += 1
    await audit(db, user, "import", "property", None, {"created": created})
    await db.commit()
    return {"created": created, "errors": errors}


class ParseIn(BaseModel):
    text: str


@router.post("/ai/parse-message")
async def parse_whatsapp_message(body: ParseIn, user: User = Depends(get_current_user),
                                 db: AsyncSession = Depends(get_db)):
    """Paste a WhatsApp message -> structured property/requirement DRAFT (not saved; UI confirms)."""
    agency = (await db.execute(select(Agency).where(Agency.id == user.agency_id))).scalar_one()
    return parse_message(body.text, agency.default_currency)
