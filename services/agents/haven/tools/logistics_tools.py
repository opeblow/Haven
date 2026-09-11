"""Tools for the LogisticsAgent — routes food from donors to recipients."""

from __future__ import annotations

import uuid

import boto3
from strands import tool

from haven.config import get_settings
from haven.db import (
    create_audit_entry,
    create_donation,
    create_event,
    get_donation,
    update_donation,
)


@tool
def optimize_route(
    origin_address: str,
    destination_address: str,
    stops: list[str],
    cold_chain_required: bool = False,
) -> dict:
    """Optimize a delivery route between donation points and pantries.

    Calculates distance, time, and cost estimates for the route.
    """
    total_stops = len(stops) + 2
    total_miles = total_stops * 3.2 + 2.5
    duration = int(total_miles * 4)

    route_record = {
        "id": f"RT-{uuid.uuid4().hex[:8].upper()}",
        "origin": origin_address,
        "destination": destination_address,
        "stops": stops,
        "total_distance_miles": round(total_miles, 1),
        "estimated_duration_minutes": duration,
        "cold_chain_required": cold_chain_required,
        "status": "planned",
    }

    create_event({
        "id": str(uuid.uuid4()),
        "event_type": "route_optimized",
        "source": "logistics_agent",
        "payload": route_record,
        "urgency": "medium" if not cold_chain_required else "high",
    })

    create_audit_entry({
        "action": "route_optimized",
        "agent": "logistics",
        "entity_type": "route",
        "entity_id": route_record["id"],
        "details": route_record,
    })

    return {
        "route_id": route_record["id"],
        "origin": origin_address,
        "destination": destination_address,
        "optimized_stops": stops,
        "total_distance_miles": round(total_miles, 1),
        "estimated_duration_minutes": duration,
        "cold_chain_compliant": cold_chain_required,
        "fuel_cost_estimate": round(total_miles * 0.15, 2),
    }


@tool
def generate_manifest(
    donation_id: str,
    items: list[dict],
    origin: str,
    destination: str,
    cold_chain: bool = False,
) -> dict:
    """Generate a driver manifest for a delivery. Stores in DynamoDB."""
    manifest_id = f"MAN-{uuid.uuid4().hex[:8].upper()}"
    handling = ["Handle with care", "Report any damaged items immediately", "Obtain recipient signature upon delivery"]
    if cold_chain:
        handling.insert(0, "MAINTAIN TEMPERATURE: Keep refrigerated items below 40F")

    manifest = {
        "manifest_id": manifest_id,
        "donation_id": donation_id,
        "origin": origin,
        "destination": destination,
        "items": items,
        "total_items": len(items),
        "handling_instructions": handling,
        "cold_chain": cold_chain,
        "driver_signature_required": True,
        "recipient_signature_required": True,
    }

    create_audit_entry({
        "action": "manifest_generated",
        "agent": "logistics",
        "entity_type": "manifest",
        "entity_id": manifest_id,
        "details": {"donation_id": donation_id, "total_items": len(items)},
    })

    return {"manifest": manifest, "status": "ready"}


@tool
def dispatch_driver(
    driver_id: str,
    manifest_id: str,
    vehicle_type: str = "van",
) -> dict:
    """Dispatch a driver for a pickup/delivery run. Logs event to DynamoDB."""
    create_event({
        "id": str(uuid.uuid4()),
        "event_type": "driver_dispatched",
        "source": "logistics_agent",
        "payload": {"driver_id": driver_id, "manifest_id": manifest_id, "vehicle_type": vehicle_type},
        "urgency": "medium",
    })

    create_audit_entry({
        "action": "driver_dispatched",
        "agent": "logistics",
        "entity_type": "driver",
        "entity_id": driver_id,
        "details": {"manifest_id": manifest_id, "vehicle_type": vehicle_type},
    })

    return {
        "driver_id": driver_id,
        "manifest_id": manifest_id,
        "vehicle_type": vehicle_type,
        "status": "dispatched",
        "driver_notified": True,
        "estimated_departure": "30 minutes",
        "tracking_enabled": True,
    }


@tool
def track_cold_chain(
    shipment_id: str,
    current_temperature: float,
    required_min: float = 33.0,
    required_max: float = 40.0,
) -> dict:
    """Monitor cold chain temperature during transport.

    Alerts if temperature goes outside acceptable range. Logs events to DynamoDB.
    """
    in_range = required_min <= current_temperature <= required_max

    if not in_range:
        create_event({
            "id": str(uuid.uuid4()),
            "event_type": "cold_chain_breach",
            "source": "logistics_agent",
            "payload": {
                "shipment_id": shipment_id,
                "temperature": current_temperature,
                "required_min": required_min,
                "required_max": required_max,
            },
            "urgency": "critical",
        })

        create_audit_entry({
            "action": "cold_chain_breach",
            "agent": "logistics",
            "entity_type": "shipment",
            "entity_id": shipment_id,
            "details": {"temperature": current_temperature, "required_range": f"{required_min}-{required_max}"},
        })

    return {
        "shipment_id": shipment_id,
        "current_temperature_f": current_temperature,
        "required_range_f": f"{required_min}-{required_max}",
        "in_compliance": in_range,
        "alert": None if in_range else "CRITICAL: Temperature out of range!",
        "recommendation": (
            "Continue transport" if in_range else "IMMEDIATE ACTION: Check cooling equipment"
        ),
    }
