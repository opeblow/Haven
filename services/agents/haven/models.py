"""Pydantic models for Haven domain objects."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class DonationStatus(str, Enum):
    OFFERED = "offered"
    ACCEPTED = "accepted"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    DISTRIBUTED = "distributed"
    REJECTED = "rejected"


class VolunteerStatus(str, Enum):
    AVAILABLE = "available"
    MATCHED = "matched"
    ON_SHIFT = "on_shift"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class ShiftStatus(str, Enum):
    OPEN = "open"
    FILLED = "filled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DonorOffer(BaseModel):
    """A food donation offer from a donor."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    donor_name: str
    donor_phone: str
    donor_email: str = ""
    description: str
    quantity: str
    category: str  # produce, dairy, protein, bakery, canned, other
    requires_refrigeration: bool = False
    expires_at: datetime | None = None
    pickup_window_start: datetime | None = None
    pickup_window_end: datetime | None = None
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    status: DonationStatus = DonationStatus.OFFERED
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Volunteer(BaseModel):
    """A registered volunteer."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    email: str
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["en"])
    has_vehicle: bool = False
    max_distance_miles: float = 10.0
    availability: list[str] = Field(default_factory=list)  # ISO day names
    total_shifts_completed: int = 0
    no_shows: int = 0
    rating: float = 5.0
    status: VolunteerStatus = VolunteerStatus.AVAILABLE
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RecipientRequest(BaseModel):
    """A request from someone needing aid."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone: str
    language: str = "en"
    request_text: str
    category: str = ""
    household_size: int = 1
    dietary_restrictions: list[str] = Field(default_factory=list)
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    resolved: bool = False
    assigned_pantry: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Shift(BaseModel):
    """A volunteer shift at a distribution point."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pantry_id: str
    pantry_name: str
    role: str  # sorting, driving, distribution, admin
    start_time: datetime
    end_time: datetime
    volunteers_needed: int = 1
    volunteers_assigned: list[str] = Field(default_factory=list)
    status: ShiftStatus = ShiftStatus.OPEN
    requirements: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LogisticsRoute(BaseModel):
    """A routing plan for food distribution."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    donation_id: str
    origin: str
    destination: str
    driver_id: str | None = None
    estimated_duration_minutes: int = 0
    distance_miles: float = 0.0
    cold_chain_required: bool = False
    temperature_range: str = ""
    stops: list[str] = Field(default_factory=list)
    status: str = "planned"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentEvent(BaseModel):
    """An event flowing through the agent swarm."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    source: str
    payload: dict = Field(default_factory=dict)
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    requires_human: bool = False
    processed_by: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
