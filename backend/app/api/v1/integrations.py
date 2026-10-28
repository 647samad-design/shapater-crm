"""Integrations & Keys: owners manage third-party credentials. Values are encrypted at rest,
lists only ever show a masked tail, and revealing/copying is owner-only and audited."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned, require_roles
from app.core.crypto import decrypt, encrypt
from app.core.db import get_db
from app.models import ApiKey, User
from app.services.audit import audit

router = APIRouter(prefix="/integrations", tags=["integrations"])
owner_only = require_roles("owner")

# Provider catalog: label for the UI, expected prefixes (soft check), and a hint.
PROVIDERS: dict[str, dict] = {
    "stripe": {"name": "Stripe", "prefixes": ["sk_live_", "sk_test_", "pk_live_", "pk_test_", "rk_live_", "rk_test_", "whsec_"],
               "hint": "Secret key (sk_…), publishable key (pk_…) or webhook secret (whsec_…)"},
    "whatsapp": {"name": "WhatsApp Cloud API", "prefixes": [], "hint": "Permanent access token from Meta"},
    "anthropic": {"name": "Anthropic (Claude)", "prefixes": ["sk-ant-"], "hint": "API key from console.anthropic.com"},
    "openai": {"name": "OpenAI", "prefixes": ["sk-"], "hint": "API key from platform.openai.com"},
    "hubspot": {"name": "HubSpot", "prefixes": ["pat-"], "hint": "Private app access token"},
    "google_maps": {"name": "Google Maps", "prefixes": ["AIza"], "hint": "Maps JavaScript / Places API key"},
    "cloudinary": {"name": "Cloudinary", "prefixes": [], "hint": "API secret"},
    "aws_s3": {"name": "AWS S3", "prefixes": [], "hint": "Secret access key"},
    "sendgrid": {"name": "SendGrid", "prefixes": ["SG."], "hint": "API key"},
    "twilio": {"name": "Twilio", "prefixes": [], "hint": "Auth token"},
    "custom": {"name": "Other", "prefixes": [], "hint": "Any other secret"},
}


class KeyIn(BaseModel):
    provider: str
    label: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=8, max_length=4096)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("provider")
    @classmethod
    def _provider(cls, v: str) -> str:
        v = v.lower()
        if v not in PROVIDERS:
            raise ValueError(f"Unknown provider. Choose one of: {', '.join(PROVIDERS)}")
        return v

    @field_validator("value", "label")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class KeyUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=100)
    value: str | None = Field(default=None, min_length=8, max_length=4096)
    notes: str | None = Field(default=None, max_length=500)


class KeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    provider: str
    label: str
    masked: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    warning: str | None = None


def _out(k: ApiKey, warning: str | None = None) -> KeyOut:
    return KeyOut(id=k.id, provider=k.provider, label=k.label, masked="••••••••" + k.last4, notes=k.notes,
                  created_at=k.created_at, updated_at=k.updated_at, warning=warning)


def _warn(provider: str, value: str) -> str | None:
    prefixes = PROVIDERS[provider]["prefixes"]
    if prefixes and not value.startswith(tuple(prefixes)):
        return f"This does not look like a {PROVIDERS[provider]['name']} key (expected to start with {', '.join(prefixes[:3])}…). Saved anyway."
    return None


@router.get("/providers")
async def providers(_: User = Depends(owner_only)):
    return [{"id": k, "name": v["name"], "hint": v["hint"]} for k, v in PROVIDERS.items()]


@router.get("/keys", response_model=list[KeyOut])
async def list_keys(user: User = Depends(owner_only), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ApiKey).where(ApiKey.agency_id == user.agency_id)
                             .order_by(ApiKey.provider, ApiKey.label))).scalars().all()
    return [_out(k) for k in rows]


@router.post("/keys", response_model=KeyOut, status_code=201)
async def add_key(data: KeyIn, user: User = Depends(owner_only), db: AsyncSession = Depends(get_db)):
    key = ApiKey(agency_id=user.agency_id, provider=data.provider, label=data.label, encrypted_value=encrypt(data.value),
                 last4=data.value[-4:], notes=data.notes, created_by=user.id)
    db.add(key)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"You already have a {PROVIDERS[data.provider]['name']} key named “{data.label}”. Edit it or choose another label.")
    await audit(db, user, "key_create", "api_key", key.id, {"provider": data.provider, "label": data.label})
    await db.commit()
    return _out(key, _warn(data.provider, data.value))


@router.patch("/keys/{key_id}", response_model=KeyOut)
async def edit_key(key_id: uuid.UUID, data: KeyUpdate, user: User = Depends(owner_only), db: AsyncSession = Depends(get_db)):
    key = await get_owned(db, ApiKey, key_id, user)
    changed = []
    if data.label is not None and data.label.strip() != key.label:
        key.label = data.label.strip(); changed.append("label")
    if data.notes is not None:
        key.notes = data.notes or None; changed.append("notes")
    warning = None
    if data.value is not None:
        value = data.value.strip()
        key.encrypted_value, key.last4 = encrypt(value), value[-4:]
        warning = _warn(key.provider, value); changed.append("value")
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Another key with this label already exists for this provider.")
    await audit(db, user, "key_update", "api_key", key.id, {"provider": key.provider, "label": key.label, "changed": changed})
    await db.commit()
    return _out(key, warning)


@router.delete("/keys/{key_id}", status_code=204)
async def delete_key(key_id: uuid.UUID, user: User = Depends(owner_only), db: AsyncSession = Depends(get_db)):
    key = await get_owned(db, ApiKey, key_id, user)
    await audit(db, user, "key_delete", "api_key", key.id, {"provider": key.provider, "label": key.label})
    await db.delete(key)
    await db.commit()


@router.post("/keys/{key_id}/reveal")
async def reveal_key(key_id: uuid.UUID, response: Response, user: User = Depends(owner_only), db: AsyncSession = Depends(get_db)):
    """Return the plaintext (for the Copy / Show buttons). POST + no-store so it is never cached. Audited."""
    key = await get_owned(db, ApiKey, key_id, user)
    try:
        value = decrypt(key.encrypted_value)
    except ValueError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    await audit(db, user, "key_reveal", "api_key", key.id, {"provider": key.provider, "label": key.label})
    await db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"value": value}
