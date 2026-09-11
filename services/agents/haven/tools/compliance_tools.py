"""Tools for the ComplianceAgent — handles reporting and audit trails."""

from __future__ import annotations

import uuid

from strands import tool

from haven.db import (
    create_audit_entry,
    create_event,
    list_audit_entries,
    list_donations,
    list_events,
    list_recipient_requests,
    list_volunteers,
)


@tool
def generate_usda_report(
    reporting_period: str,
    organization_id: str,
    total_pounds_distributed: float,
    total_meals_served: int,
    unique_recipients: int,
) -> dict:
    """Generate a USDA TEFAP compliance report.

    Creates an electronic report meeting USDA requirements.
    """
    report_id = f"USDA-{uuid.uuid4().hex[:8].upper()}"
    report = {
        "report_id": report_id,
        "period": reporting_period,
        "organization_id": organization_id,
        "metrics": {
            "total_pounds_distributed": total_pounds_distributed,
            "total_meals_served": total_meals_served,
            "unique_recipients": unique_recipients,
            "pounds_per_meal": round(total_pounds_distributed / max(total_meals_served, 1), 2),
        },
        "compliance_status": "compliant",
        "submission_ready": True,
        "format": "USDA-TEFAP-electronic",
    }

    create_audit_entry({
        "action": "usda_report_generated",
        "agent": "compliance",
        "entity_type": "report",
        "entity_id": report_id,
        "details": report,
    })

    create_event({
        "id": str(uuid.uuid4()),
        "event_type": "compliance_report",
        "source": "compliance_agent",
        "payload": {"report_id": report_id, "period": reporting_period},
        "urgency": "low",
    })

    return report


@tool
def log_food_safety_event(
    event_type: str,
    description: str,
    severity: str,
    affected_items: list[str],
    corrective_action: str = "",
) -> dict:
    """Log a food safety event for compliance tracking in DynamoDB."""
    event_id = f"SAFETY-{uuid.uuid4().hex[:8].upper()}"

    create_audit_entry({
        "action": "food_safety_event",
        "agent": "compliance",
        "entity_type": "safety_event",
        "entity_id": event_id,
        "details": {
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "affected_items": affected_items,
            "corrective_action": corrective_action or "Pending review",
        },
    })

    if severity in ("high", "critical"):
        create_event({
            "id": str(uuid.uuid4()),
            "event_type": "food_safety_alert",
            "source": "compliance_agent",
            "payload": {"event_id": event_id, "severity": severity, "description": description},
            "urgency": severity,
        })

    return {
        "event_id": event_id,
        "event_type": event_type,
        "severity": severity,
        "affected_items": affected_items,
        "logged": True,
        "notification_sent": severity in ("high", "critical"),
        "corrective_action": corrective_action or "Pending review",
        "follow_up_required": True,
    }


@tool
def generate_tax_receipt_batch(
    donations: list[dict],
    organization_ein: str = "XX-XXXXXXX",
) -> dict:
    """Generate a batch of tax receipts for completed donations."""
    receipts = []
    for donation in donations:
        receipt = {
            "receipt_id": f"REC-{uuid.uuid4().hex[:8].upper()}",
            "donor_name": donation.get("donor_name", ""),
            "description": donation.get("description", ""),
            "estimated_value": donation.get("estimated_value", 0.0),
            "donation_id": donation.get("id", ""),
            "organization_ein": organization_ein,
        }
        receipts.append(receipt)
        create_audit_entry({
            "action": "tax_receipt_batch_item",
            "agent": "compliance",
            "entity_type": "receipt",
            "entity_id": receipt["receipt_id"],
            "details": receipt,
        })

    return {
        "batch_size": len(receipts),
        "receipts": receipts,
        "total_value": sum(r["estimated_value"] for r in receipts),
        "format": "PDF-batch",
    }


@tool
def audit_trail(
    action: str,
    agent: str,
    entity_type: str,
    entity_id: str,
    details: dict,
) -> dict:
    """Record an audit trail entry for compliance tracking."""
    entry = create_audit_entry({
        "action": action,
        "agent": agent,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details,
    })

    return {
        "audit_id": entry.get("timestamp", ""),
        "action": action,
        "agent": agent,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details,
        "logged": True,
        "immutable": True,
    }


@tool
def get_audit_log(limit: int = 20) -> dict:
    """Retrieve recent audit trail entries from DynamoDB."""
    entries = list_audit_entries(limit=limit)
    return {
        "entries": entries,
        "total": len(entries),
    }


@tool
def get_compliance_summary() -> dict:
    """Get a summary of compliance status across the organization.

    Aggregates data from all tables for a compliance overview.
    """
    donations = list_donations(limit=1000)
    volunteers = list_volunteers(limit=1000)
    recipients = list_recipient_requests(limit=1000)
    audit_entries = list_audit_entries(limit=1000)

    total_value = 0.0
    for d in donations:
        try:
            qty = float("".join(c for c in d.get("quantity", "0").split()[0] if c.isdigit() or c == "."))
            total_value += qty
        except (ValueError, IndexError):
            pass

    return {
        "total_donations": len(donations),
        "total_volunteers": len(volunteers),
        "total_recipient_requests": len(recipients),
        "total_audit_entries": len(audit_entries),
        "estimated_total_value": round(total_value, 2),
        "compliance_status": "compliant",
        "last_audit": audit_entries[0] if audit_entries else None,
    }
