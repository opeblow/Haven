"""DynamoDB database access layer for Haven."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from haven.config import get_settings


def get_dynamodb_resource():
    """Get a DynamoDB resource, using local endpoint if configured."""
    settings = get_settings()
    kwargs: dict[str, Any] = {"region_name": settings.aws_region}
    endpoint_url = getattr(settings, "dynamodb_endpoint_url", "")
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.resource("dynamodb", **kwargs)


def get_table(table_name: str):
    """Get a DynamoDB table reference."""
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(table_name)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Donations ──────────────────────────────────────────────────────────────


def create_donation(donation: dict) -> dict:
    """Insert a new donation record into DynamoDB."""
    settings = get_settings()
    table = get_table(settings.donations_table)
    record = {**donation, "created_at": _now_iso(), "updated_at": _now_iso()}
    table.put_item(Item=record)
    return record


def get_donation(donation_id: str) -> dict | None:
    """Get a single donation by ID."""
    settings = get_settings()
    table = get_table(settings.donations_table)
    resp = table.get_item(Key={"id": donation_id})
    return resp.get("Item")


def update_donation(donation_id: str, updates: dict) -> dict | None:
    """Update fields on a donation record."""
    settings = get_settings()
    table = get_table(settings.donations_table)
    updates["updated_at"] = _now_iso()
    expr_parts = []
    expr_names = {}
    expr_values = {}
    for i, (k, v) in enumerate(updates.items()):
        alias = f"#f{i}"
        val_alias = f":v{i}"
        expr_parts.append(f"{alias} = {val_alias}")
        expr_names[alias] = k
        expr_values[val_alias] = v
    table.update_item(
        Key={"id": donation_id},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    return get_donation(donation_id)


def list_donations(status: str | None = None, limit: int = 50) -> list[dict]:
    """List donations, optionally filtered by status."""
    settings = get_settings()
    table = get_table(settings.donations_table)
    if status:
        resp = table.query(
            IndexName="status-index",
            KeyConditionExpression=Key("status").eq(status),
            Limit=limit,
            ScanIndexForward=False,
        )
    else:
        resp = table.scan(Limit=limit)
    return resp.get("Items", [])


def get_donation_stats() -> dict:
    """Get aggregated donation statistics."""
    settings = get_settings()
    table = get_table(settings.donations_table)
    resp = table.scan()
    items = resp.get("Items", [])
    total = len(items)
    by_status: dict[str, int] = {}
    total_lbs = 0.0
    for item in items:
        s = item.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        qty = item.get("quantity", "")
        try:
            num = float("".join(c for c in qty.split()[0] if c.isdigit() or c == "."))
            total_lbs += num
        except (ValueError, IndexError):
            pass
    return {
        "total_donations": total,
        "by_status": by_status,
        "total_lbs": round(total_lbs, 1),
    }


# ── Volunteers ─────────────────────────────────────────────────────────────


def create_volunteer(volunteer: dict) -> dict:
    """Insert a new volunteer record."""
    settings = get_settings()
    table = get_table(settings.volunteers_table)
    record = {**volunteer, "created_at": _now_iso()}
    table.put_item(Item=record)
    return record


def get_volunteer(volunteer_id: str) -> dict | None:
    """Get a single volunteer by ID."""
    settings = get_settings()
    table = get_table(settings.volunteers_table)
    resp = table.get_item(Key={"id": volunteer_id})
    return resp.get("Item")


def update_volunteer(volunteer_id: str, updates: dict) -> dict | None:
    """Update fields on a volunteer record."""
    settings = get_settings()
    table = get_table(settings.volunteers_table)
    expr_parts = []
    expr_names = {}
    expr_values = {}
    for i, (k, v) in enumerate(updates.items()):
        alias = f"#f{i}"
        val_alias = f":v{i}"
        expr_parts.append(f"{alias} = {val_alias}")
        expr_names[alias] = k
        expr_values[val_alias] = v
    table.update_item(
        Key={"id": volunteer_id},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    return get_volunteer(volunteer_id)


def list_volunteers(status: str | None = None, limit: int = 50) -> list[dict]:
    """List volunteers, optionally filtered by status."""
    settings = get_settings()
    table = get_table(settings.volunteers_table)
    if status:
        resp = table.query(
            IndexName="status-index",
            KeyConditionExpression=Key("status").eq(status),
            Limit=limit,
            ScanIndexForward=False,
        )
    else:
        resp = table.scan(Limit=limit)
    return resp.get("Items", [])


# ── Recipient Requests ─────────────────────────────────────────────────────


def create_recipient_request(request: dict) -> dict:
    """Insert a new recipient request."""
    settings = get_settings()
    table = get_table(settings.recipients_table)
    record = {**request, "created_at": _now_iso()}
    table.put_item(Item=record)
    return record


def get_recipient_request(request_id: str) -> dict | None:
    """Get a single recipient request by ID."""
    settings = get_settings()
    table = get_table(settings.recipients_table)
    resp = table.get_item(Key={"id": request_id})
    return resp.get("Item")


def update_recipient_request(request_id: str, updates: dict) -> dict | None:
    """Update fields on a recipient request."""
    settings = get_settings()
    table = get_table(settings.recipients_table)
    expr_parts = []
    expr_names = {}
    expr_values = {}
    for i, (k, v) in enumerate(updates.items()):
        alias = f"#f{i}"
        val_alias = f":v{i}"
        expr_parts.append(f"{alias} = {val_alias}")
        expr_names[alias] = k
        expr_values[val_alias] = v
    table.update_item(
        Key={"id": request_id},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    return get_recipient_request(request_id)


def list_recipient_requests(resolved: bool | None = None, limit: int = 50) -> list[dict]:
    """List recipient requests, optionally filtered by resolved status."""
    settings = get_settings()
    table = get_table(settings.recipients_table)
    if resolved is not None:
        resp = table.query(
            IndexName="resolved-index",
            KeyConditionExpression=Key("resolved").eq(resolved),
            Limit=limit,
            ScanIndexForward=False,
        )
    else:
        resp = table.scan(Limit=limit)
    return resp.get("Items", [])


# ── Shifts ─────────────────────────────────────────────────────────────────


def create_shift(shift: dict) -> dict:
    """Insert a new shift record."""
    settings = get_settings()
    table = get_table(settings.shifts_table)
    record = {**shift, "created_at": _now_iso()}
    table.put_item(Item=record)
    return record


def get_shift(shift_id: str) -> dict | None:
    """Get a single shift by ID."""
    settings = get_settings()
    table = get_table(settings.shifts_table)
    resp = table.get_item(Key={"id": shift_id})
    return resp.get("Item")


def update_shift(shift_id: str, updates: dict) -> dict | None:
    """Update fields on a shift record."""
    settings = get_settings()
    table = get_table(settings.shifts_table)
    expr_parts = []
    expr_names = {}
    expr_values = {}
    for i, (k, v) in enumerate(updates.items()):
        alias = f"#f{i}"
        val_alias = f":v{i}"
        expr_parts.append(f"{alias} = {val_alias}")
        expr_names[alias] = k
        expr_values[val_alias] = v
    table.update_item(
        Key={"id": shift_id},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
    return get_shift(shift_id)


def list_shifts(status: str | None = None, pantry_id: str | None = None, limit: int = 50) -> list[dict]:
    """List shifts, optionally filtered."""
    settings = get_settings()
    table = get_table(settings.shifts_table)
    if status:
        resp = table.query(
            IndexName="status-index",
            KeyConditionExpression=Key("status").eq(status),
            Limit=limit,
            ScanIndexForward=False,
        )
    else:
        resp = table.scan(Limit=limit)
    items = resp.get("Items", [])
    if pantry_id:
        items = [i for i in items if i.get("pantry_id") == pantry_id]
    return items


# ── Events ─────────────────────────────────────────────────────────────────


def create_event(event: dict) -> dict:
    """Insert a new event record."""
    settings = get_settings()
    table = get_table(settings.events_table)
    record = {**event, "created_at": _now_iso()}
    table.put_item(Item=record)
    return record


def list_events(limit: int = 50) -> list[dict]:
    """List recent events, newest first."""
    settings = get_settings()
    table = get_table(settings.events_table)
    resp = table.scan(Limit=limit)
    items = resp.get("Items", [])
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items[:limit]


# ── Audit Trail ────────────────────────────────────────────────────────────


def create_audit_entry(entry: dict) -> dict:
    """Insert an immutable audit trail entry."""
    settings = get_settings()
    table = get_table(settings.audit_table)
    record = {**entry, "timestamp": _now_iso()}
    table.put_item(Item=record)
    return record


def list_audit_entries(limit: int = 50) -> list[dict]:
    """List recent audit entries, newest first."""
    settings = get_settings()
    table = get_table(settings.audit_table)
    resp = table.scan(Limit=limit)
    items = resp.get("Items", [])
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items[:limit]


def get_dashboard_stats() -> dict:
    """Get aggregated dashboard statistics from all tables."""
    donation_stats = get_donation_stats()
    volunteers = list_volunteers(limit=1000)
    shifts = list_shifts(limit=1000)
    recipients = list_recipient_requests(limit=1000)

    active_volunteers = len([v for v in volunteers if v.get("status") in ("available", "on_shift", "matched")])
    open_shifts = len([s for s in shifts if s.get("status") in ("open", "filled")])
    total_shifts = len(shifts)
    resolved_requests = len([r for r in recipients if r.get("resolved")])

    return {
        "total_donations": donation_stats["total_donations"],
        "donations_by_status": donation_stats["by_status"],
        "total_lbs_distributed": donation_stats["total_lbs"],
        "active_volunteers": active_volunteers,
        "total_volunteers": len(volunteers),
        "open_shifts": open_shifts,
        "total_shifts": total_shifts,
        "total_recipient_requests": len(recipients),
        "resolved_requests": resolved_requests,
    }
