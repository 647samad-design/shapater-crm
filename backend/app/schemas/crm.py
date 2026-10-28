import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Purpose = Literal["sale", "rent"]
AreaUnit = Literal["sqft", "sqm", "sqyd", "marla", "kanal"]
PropertyStatus = Literal["available", "sold", "rented", "hold"]
Stage = Literal["new", "contacted", "viewing", "negotiation", "won", "lost"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Properties ----------
class PropertyCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    description: str | None = None
    purpose: Purpose
    property_type: str
    price: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    area_value: float | None = Field(default=None, gt=0)
    area_unit: AreaUnit | None = None
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    country: str = "PK"
    city: str | None = None
    area_name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    features: list[str] = []
    owner_name: str | None = None
    owner_phone: str | None = None
    permit_number: str | None = None


class PropertyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    purpose: Purpose | None = None
    property_type: str | None = None
    status: PropertyStatus | None = None
    price: float | None = Field(default=None, gt=0)
    currency: str | None = None
    area_value: float | None = None
    area_unit: AreaUnit | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    city: str | None = None
    area_name: str | None = None
    address: str | None = None
    features: list[str] | None = None
    owner_name: str | None = None
    owner_phone: str | None = None
    permit_number: str | None = None


class PropertyOut(ORM, PropertyCreate):
    id: uuid.UUID
    status: str
    area_sqft: float | None
    created_at: datetime


# ---------- Clients ----------
class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=5, max_length=40)
    email: str | None = None
    source: str | None = None
    notes: str | None = None
    assigned_to: uuid.UUID | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    source: str | None = None
    notes: str | None = None
    assigned_to: uuid.UUID | None = None


class ClientOut(ORM):
    id: uuid.UUID
    name: str
    phone: str
    phone_normalized: str
    email: str | None
    source: str | None
    notes: str | None
    assigned_to: uuid.UUID | None
    created_at: datetime


# ---------- Requirements ----------
class RequirementCreate(BaseModel):
    client_id: uuid.UUID
    purpose: Purpose
    property_types: list[str] = []
    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)
    currency: str = Field(min_length=3, max_length=3)
    city: str | None = None
    preferred_areas: list[str] = []
    bedrooms_min: int | None = Field(default=None, ge=0)
    bedrooms_max: int | None = Field(default=None, ge=0)
    required_features: list[str] = []
    urgency: Literal["low", "medium", "high"] = "medium"
    notes: str | None = None


class RequirementUpdate(BaseModel):
    purpose: Purpose | None = None
    property_types: list[str] | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    currency: str | None = None
    city: str | None = None
    preferred_areas: list[str] | None = None
    bedrooms_min: int | None = None
    bedrooms_max: int | None = None
    required_features: list[str] | None = None
    urgency: Literal["low", "medium", "high"] | None = None
    notes: str | None = None
    is_active: bool | None = None


class RequirementOut(ORM, RequirementCreate):
    id: uuid.UUID
    is_active: bool
    created_at: datetime


# ---------- Matches ----------
class MatchOut(ORM):
    id: uuid.UUID
    requirement_id: uuid.UUID
    property_id: uuid.UUID
    score: int
    breakdown: dict
    status: str
    created_at: datetime


class MatchStatusUpdate(BaseModel):
    status: Literal["new", "sent", "viewed", "rejected"]


# ---------- Leads & activities ----------
class LeadCreate(BaseModel):
    client_id: uuid.UUID
    requirement_id: uuid.UUID | None = None
    property_id: uuid.UUID | None = None
    source: str | None = None
    assigned_to: uuid.UUID | None = None
    value: float | None = None
    currency: str | None = None


class LeadUpdate(BaseModel):
    stage: Stage | None = None
    assigned_to: uuid.UUID | None = None
    value: float | None = None
    currency: str | None = None
    property_id: uuid.UUID | None = None


class LeadOut(ORM):
    id: uuid.UUID
    client_id: uuid.UUID
    requirement_id: uuid.UUID | None
    property_id: uuid.UUID | None
    stage: str
    source: str | None
    assigned_to: uuid.UUID | None
    value: float | None
    currency: str | None
    created_at: datetime


class ActivityCreate(BaseModel):
    type: Literal["call", "note", "meeting", "viewing", "follow_up"]
    note: str | None = None
    due_at: datetime | None = None


class ActivityOut(ORM):
    id: uuid.UUID
    lead_id: uuid.UUID | None
    user_id: uuid.UUID
    type: str
    note: str | None
    due_at: datetime | None
    done: bool
    created_at: datetime
