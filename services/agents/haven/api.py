"""FastAPI application — thin API layer for Haven agents."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, Any

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from haven.agents.supervisor import Supervisor
from haven.config import get_settings
from haven.db import (
    create_volunteer,
    delete_recipient_request,
    get_dashboard_stats,
    get_donation,
    list_audit_entries,
    list_donations,
    list_events,
    list_recipient_requests,
    list_shifts,
    list_volunteers,
)

logger = structlog.get_logger()
settings = get_settings()

supervisor: Supervisor | None = None


# ── Auth helpers ───────────────────────────────────────────────────────────


async def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    """FastAPI dependency that validates an API key when one is configured.

    When HAVEN_API_KEY is empty or unset the check is skipped (dev mode).
    """
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return x_api_key or ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and clean up resources."""
    global supervisor
    logger.info("haven.api.starting")
    supervisor = Supervisor()
    logger.info("haven.api.started")
    yield
    logger.info("haven.api.shutting_down")


app = FastAPI(
    title="Haven API",
    description="Autonomous operations for community aid organizations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ─────────────────────────────────────────────────────────


class DonationOfferRequest(BaseModel):
    donor_name: str
    donor_phone: str
    description: str
    quantity: str
    category: str = "other"
    requires_refrigeration: bool = False
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    source: str = "web"


class RecipientRequestModel(BaseModel):
    phone: str
    request_text: str
    language: str = "en"
    latitude: float = 0.0
    longitude: float = 0.0
    household_size: int = 1
    dietary_restrictions: list[str] = []
    source: str = "sms"


class VolunteerInquiryModel(BaseModel):
    name: str
    phone: str
    email: str = ""
    skills: list[str] = []
    languages: list[str] = ["en"]
    has_vehicle: bool = False
    source: str = "web"


class ShiftCreateModel(BaseModel):
    pantry_id: str
    pantry_name: str
    role: str
    start_time: str
    end_time: str
    volunteers_needed: int = 1
    requirements: list[str] = []


# ── Health ─────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint showing all agents alive."""
    if supervisor is None:
        raise HTTPException(status_code=503, detail="Supervisor not initialized")
    status = await supervisor.get_status()
    return {
        "status": "healthy",
        "service": "haven-agents",
        "version": "0.1.0",
        **status,
    }


# ── Donations ──────────────────────────────────────────────────────────────


@app.post("/api/donations/offer")
async def submit_donation_offer(
    request: DonationOfferRequest,
    _api_key: Annotated[str, Depends(require_api_key)],
) -> dict[str, Any]:
    """Submit a new donation offer for processing."""
    if supervisor is None:
        raise HTTPException(status_code=503, detail="Supervisor not initialized")
    result = await supervisor.handle_donation_offer(request.model_dump())
    return {"success": True, "result": result}


@app.get("/api/donations")
async def get_donations(status: str | None = None, limit: int = 50) -> dict[str, Any]:
    """List all donations from DynamoDB."""
    donations = list_donations(status=status, limit=limit)
    return {"donations": donations, "total": len(donations)}


@app.get("/api/donations/{donation_id}")
async def get_donation_detail(donation_id: str) -> dict[str, Any]:
    """Get a single donation by ID from DynamoDB."""
    donation = get_donation(donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation


# ── Recipients ─────────────────────────────────────────────────────────────


@app.post("/api/recipients/request")
async def submit_recipient_request(
    request: RecipientRequestModel,
    _api_key: Annotated[str, Depends(require_api_key)],
) -> dict[str, Any]:
    """Submit a request from someone seeking aid."""
    if supervisor is None:
        raise HTTPException(status_code=503, detail="Supervisor not initialized")
    result = await supervisor.handle_recipient_request(request.model_dump())
    return {"success": True, "result": result}


@app.delete("/api/recipients/{request_id}")
async def delete_recipient_endpoint(
    request_id: str,
    _api_key: Annotated[str, Depends(require_api_key)],
) -> dict[str, Any]:
    """Delete a recipient request by ID."""
    deleted = delete_recipient_request(request_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipient request not found")
    return {"success": True, "deleted_id": request_id}


@app.get("/api/recipients")
async def get_recipient_requests(resolved: bool | None = None, limit: int = 50) -> dict[str, Any]:
    """List recipient requests from DynamoDB."""
    requests = list_recipient_requests(resolved=resolved, limit=limit)
    return {"requests": requests, "total": len(requests)}


# ── Volunteers ─────────────────────────────────────────────────────────────


@app.post("/api/volunteers/inquiry")
async def submit_volunteer_inquiry(
    request: VolunteerInquiryModel,
    _api_key: Annotated[str, Depends(require_api_key)],
) -> dict[str, Any]:
    """Submit a volunteer inquiry. Stores in DynamoDB."""
    import uuid

    volunteer_data = {
        "id": str(uuid.uuid4()),
        **request.model_dump(),
        "total_shifts_completed": 0,
        "no_shows": 0,
        "rating": 5.0,
        "status": "available",
        "max_distance_miles": 10.0,
        "availability": [],
    }
    create_volunteer(volunteer_data)

    if supervisor is None:
        raise HTTPException(status_code=503, detail="Supervisor not initialized")
    result = await supervisor.handle_volunteer_inquiry(request.model_dump())
    return {"success": True, "result": result, "volunteer_id": volunteer_data["id"]}


@app.get("/api/volunteers")
async def get_volunteers(status: str | None = None, limit: int = 50) -> dict[str, Any]:
    """List volunteers from DynamoDB."""
    volunteers = list_volunteers(status=status, limit=limit)
    return {"volunteers": volunteers, "total": len(volunteers)}


@app.post("/api/shifts")
async def create_shift_endpoint(
    request: ShiftCreateModel,
    _api_key: Annotated[str, Depends(require_api_key)],
) -> dict[str, Any]:
    """Create a new volunteer shift in DynamoDB."""
    import uuid

    from haven.db import create_shift

    shift_data = {
        "id": str(uuid.uuid4()),
        **request.model_dump(),
        "volunteers_assigned": [],
        "status": "open",
    }
    record = create_shift(shift_data)
    return {"success": True, "shift": record}


@app.get("/api/shifts")
async def get_shifts(status: str | None = None, limit: int = 50) -> dict[str, Any]:
    """List shifts from DynamoDB."""
    shifts = list_shifts(status=status, limit=limit)
    return {"shifts": shifts, "total": len(shifts)}


# ── Events ─────────────────────────────────────────────────────────────────


@app.get("/api/events/feed")
async def get_event_feed(limit: int = 50) -> dict[str, Any]:
    """Get the live event feed from DynamoDB."""
    events = list_events(limit=limit)
    return {"events": events, "total": len(events)}


# ── Stats ──────────────────────────────────────────────────────────────────


@app.get("/api/stats")
async def get_stats() -> dict[str, Any]:
    """Get dashboard statistics computed from DynamoDB data."""
    return get_dashboard_stats()


# ── Audit ──────────────────────────────────────────────────────────────────


@app.get("/api/audit")
async def get_audit(limit: int = 50) -> dict[str, Any]:
    """Get audit trail entries from DynamoDB."""
    entries = list_audit_entries(limit=limit)
    return {"entries": entries, "total": len(entries)}
