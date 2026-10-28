import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class TenantMixin:
    """Every business table carries agency_id (multi-tenancy)."""

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    agency_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("agencies.id"), index=True)


class Agency(Base, TimestampMixin):
    __tablename__ = "agencies"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(2), default="PK")
    default_currency: Mapped[str] = mapped_column(String(3), default="PKR")
    plan: Mapped[str] = mapped_column(String(30), default="trial")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    agency_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("agencies.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="agent")  # owner|manager|agent
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Property(Base, TenantMixin, TimestampMixin):
    __tablename__ = "properties"
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    purpose: Mapped[str] = mapped_column(String(10), index=True)  # sale|rent
    property_type: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)
    price: Mapped[float] = mapped_column(Numeric(16, 2))
    currency: Mapped[str] = mapped_column(String(3))
    area_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    area_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="PK")
    city: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    area_name: Mapped[str | None] = mapped_column(String(150), index=True, nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    features: Mapped[list] = mapped_column(JSON, default=list)
    owner_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    owner_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    permit_number: Mapped[str | None] = mapped_column(String(100), nullable=True)  # RERA/Trakheesi/REGA
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Client(Base, TenantMixin, TimestampMixin):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("agency_id", "phone_normalized", name="uq_client_phone_per_agency"),)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(40))
    phone_normalized: Mapped[str] = mapped_column(String(40), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # whatsapp|zameen|bayut|walk_in|referral
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Requirement(Base, TenantMixin, TimestampMixin):
    __tablename__ = "requirements"
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("clients.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(10), index=True)
    property_types: Mapped[list] = mapped_column(JSON, default=list)
    budget_min: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3))
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_areas: Mapped[list] = mapped_column(JSON, default=list)
    bedrooms_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bedrooms_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_features: Mapped[list] = mapped_column(JSON, default=list)
    urgency: Mapped[str] = mapped_column(String(10), default="medium")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class Match(Base, TenantMixin, TimestampMixin):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("requirement_id", "property_id", name="uq_match_pair"),)
    requirement_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("requirements.id"), index=True)
    property_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("properties.id"), index=True)
    score: Mapped[int] = mapped_column(Integer, index=True)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="new")  # new|sent|viewed|rejected


class Lead(Base, TenantMixin, TimestampMixin):
    __tablename__ = "leads"
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("clients.id"), index=True)
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("requirements.id"), nullable=True)
    property_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("properties.id"), nullable=True)
    stage: Mapped[str] = mapped_column(String(20), default="new", index=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    value: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)


class Activity(Base, TenantMixin, TimestampMixin):
    __tablename__ = "activities"
    lead_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("leads.id"), nullable=True, index=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("clients.id"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(20))  # call|note|meeting|viewing|follow_up
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Base, TenantMixin):
    __tablename__ = "audit_logs"
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    action: Mapped[str] = mapped_column(String(30))
    entity: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    changes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
