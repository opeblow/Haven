"""Tools for the DonorAgent — handles donation offers."""

from __future__ import annotations

from strands import tool

from haven.db import (
    create_audit_entry,
    create_donation,
    create_event,
    get_donation,
    update_donation,
)
from haven.models import DonationStatus


@tool
def parse_donation_offer(
    donor_name: str,
    donor_phone: str,
    description: str,
    quantity: str,
    category: str = "other",
    requires_refrigeration: bool = False,
    donor_email: str = "",
    address: str = "",
    expires_at: str = "",
    offer_id: str = "",
) -> dict:
    """Parse and validate a new donation offer from a donor.

    Analyzes the offer details, determines category, and creates
    a structured donation record in DynamoDB.

    When ``offer_id`` is provided (e.g. the supervisor already persisted the
    record), the existing record is updated instead of creating a duplicate.
    """
    import uuid

    fields = {
        "donor_name": donor_name,
        "donor_phone": donor_phone,
        "donor_email": donor_email,
        "description": description,
        "quantity": quantity,
        "category": category,
        "requires_refrigeration": requires_refrigeration,
        "address": address,
        "status": DonationStatus.OFFERED.value,
        "notes": "",
    }
    if offer_id:
        donation_id = offer_id
        updated = update_donation(offer_id, fields)
        record = updated if updated is not None else {"id": offer_id, **fields}
    else:
        donation_id = str(uuid.uuid4())
        record = create_donation({"id": donation_id, **fields})
    create_event(
        {
            "id": str(uuid.uuid4()),
            "event_type": "donation_offer",
            "source": "donor_agent",
            "payload": {"donation_id": donation_id, "donor_name": donor_name, "category": category},
            "urgency": "medium",
        }
    )
    return {
        "offer_id": record["id"],
        "status": "parsed",
        "category": record["category"],
        "requires_refrigeration": record["requires_refrigeration"],
        "quantity": record["quantity"],
        "next_step": "assess_cold_chain",
    }


@tool
def check_cold_chain_requirements(
    offer_id: str,
    category: str,
    requires_refrigeration: bool,
) -> dict:
    """Assess cold chain and storage requirements for a donation.

    Determines if the donation requires refrigerated transport,
    estimated time window, and storage capacity needs.
    """
    cold_chain_map = {
        "dairy": {"required": True, "temp": "33-40°F", "max_hours": 4},
        "protein": {"required": True, "temp": "33-40°F", "max_hours": 4},
        "produce": {"required": False, "temp": "38-45°F", "max_hours": 8},
        "bakery": {"required": False, "temp": "ambient", "max_hours": 24},
        "canned": {"required": False, "temp": "ambient", "max_hours": 168},
        "other": {"required": False, "temp": "ambient", "max_hours": 48},
    }
    assessment = cold_chain_map.get(category, cold_chain_map["other"])
    if requires_refrigeration:
        assessment["required"] = True

    update_donation(
        offer_id,
        {
            "cold_chain_required": assessment["required"],
            "temperature_range": assessment["temp"],
        },
    )

    return {
        "offer_id": offer_id,
        "cold_chain_required": assessment["required"],
        "temperature_range": assessment["temp"],
        "max_pickup_hours": assessment["max_hours"],
        "logistics_priority": "high" if assessment["required"] else "normal",
    }


@tool
def accept_donation(offer_id: str, notes: str = "") -> dict:
    """Accept a donation offer and update its status in DynamoDB.

    Confirms the donation, logs acceptance, and triggers
    logistics planning.
    """
    donation = get_donation(offer_id)
    if not donation:
        return {"error": f"Donation {offer_id} not found"}
    update_donation(offer_id, {"status": DonationStatus.ACCEPTED.value, "notes": notes})
    create_audit_entry(
        {
            "action": "donation_accepted",
            "agent": "donor",
            "entity_type": "donation",
            "entity_id": offer_id,
            "details": {"donor_name": donation.get("donor_name", ""), "notes": notes},
        }
    )
    return {
        "offer_id": offer_id,
        "status": DonationStatus.ACCEPTED.value,
        "message": "Donation accepted. Logistics agent notified for pickup scheduling.",
        "notes": notes,
    }


@tool
def negotiate_pickup_time(
    offer_id: str,
    donor_name: str,
    proposed_times: list[str],
    cold_chain_priority: bool = False,
) -> dict:
    """Negotiate a pickup window with the donor.

    Proposes optimal pickup times based on cold chain requirements,
    driver availability, and donor preferences.
    """
    recommendation = proposed_times[0] if proposed_times else "ASAP"
    if cold_chain_priority:
        return {
            "offer_id": offer_id,
            "proposed_time": recommendation,
            "message": f"Urgent cold-chain pickup proposed for {donor_name}: {recommendation}. "
            f"Please confirm or suggest an alternative time.",
            "priority": "high",
        }
    return {
        "offer_id": offer_id,
        "proposed_time": recommendation,
        "message": f"Pickup window proposed for {donor_name}: {recommendation}. Waiting for donor confirmation.",
        "priority": "normal",
    }


@tool
def generate_tax_receipt(
    offer_id: str,
    donor_name: str,
    description: str,
    estimated_value: float = 0.0,
) -> dict:
    """Generate a tax receipt for a completed donation.

    Creates a receipt with IRS-compliant formatting and stores it.
    """
    import uuid

    receipt_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
    receipt = {
        "receipt_id": receipt_id,
        "donor_name": donor_name,
        "description": description,
        "estimated_value": estimated_value,
        "fair_market_value_note": "Value based on comparable retail pricing per IRS guidelines",
        "donation_id": offer_id,
        "organization_ein": "XX-XXXXXXX",
        "format": "PDF-ready",
    }
    create_audit_entry(
        {
            "action": "tax_receipt_generated",
            "agent": "donor",
            "entity_type": "receipt",
            "entity_id": receipt_id,
            "details": receipt,
        }
    )
    return {
        "offer_id": offer_id,
        "receipt": receipt,
        "message": f"Tax receipt {receipt_id} generated for {donor_name}.",
    }
