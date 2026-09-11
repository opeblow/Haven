"""DynamoDB database access layer for Haven."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

import boto3
from boto3.dynamodb.conditions import Key

from haven.config import get_settings


def _encode_value(value: Any) -> Any:
    """Recursively coerce Python types to values boto3/DynamoDB accepts.

    boto3's type serializer rejects raw ``float`` and ``datetime`` values, so
    floats become ``Decimal`` (DynamoDB's only numeric type) and datetimes
    become ISO strings before any write.
    """
    if value is None or isinstance(value, (str, int, bool, Decimal)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _encode_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_encode_value(v) for v in value]
    return value


def _encode_item(record: dict) -> dict:
    """Encode a whole record dict before a DynamoDB write."""
    return {k: _encode_value(v) for k, v in record.items()}


def _extract_pounds(quantity: str) -> float | None:
    """Extract a pounds figure only when the quantity is explicitly lb/lbs/pound.

    Free-text quantities without an explicit weight unit are NOT counted so a
    value like "20 boxes" is never reported as 20 pounds distributed.
    """
    text = (quantity or "").strip().lower()
    if not text:
        return None
    if not any(u in text for u in ("lb", "pound")):
        return None
    cleaned = ""
    for ch in text.split()[0]:
        if ch.isdigit() or ch == ".":
            cleaned += ch
    try:
        return float(cleaned)
    except ValueError:
        return None


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
    return datetime.now(UTC).isoformat()


# ── Donations ──────────────────────────────────────────────────────────────


def create_donation(donation: dict) -> dict:
    """Insert a new donation record into DynamoDB."""
    settings = get_settings()
    table = get_table(settings.donations_table)
    record = {**donation, "created_at": _now_iso(), "updated_at": _now_iso()}
    table.put_item(Item=_encode_item(record))
    return record


def get_donation(donation_id: str) -> dict | None:
    """Get a single donation by ID."""
    settings = get_settings()
    table = get_table(settings.donations_table)
    resp = table.get_item(Key={"id": donation_id})
    return cast("dict[str, Any] | None", resp.get("Item"))


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
        ExpressionAttributeValues=_encode_item(expr_values),
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
    return cast("list[dict[str, Any]]", resp.get("Items", []))


def get_donation_stats() -> dict:
    """Get aggregated donation statistics."""
    settings = get_settings()
    table = get_table(settings.donations_table)
    resp = table.scan()
    items = resp.get("Items", [])
    total = len(items)
    by_status: dict[str, int] = {}
    total_lbs = 0.0
    explicit_lbs_items = 0
    for item in items:
        s = item.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        lbs = _extract_pounds(item.get("quantity", ""))
        if lbs is not None:
            total_lbs += lbs
            explicit_lbs_items += 1
    return {
        "total_donations": total,
        "by_status": by_status,
        "total_lbs": round(total_lbs, 1),
        "total_lbs_note": (
            f"Based on {explicit_lbs_items} of {total} donations with explicit lbs; "
            "non-weight quantities are not counted."
        ),
    }


# ── Volunteers ─────────────────────────────────────────────────────────────


def create_volunteer(volunteer: dict) -> dict:
    """Insert a new volunteer record."""
    settings = get_settings()
    table = get_table(settings.volunteers_table)
    record = {**volunteer, "created_at": _now_iso()}
    table.put_item(Item=_encode_item(record))
    return record


def get_volunteer(volunteer_id: str) -> dict | None:
    """Get a single volunteer by ID."""
    settings = get_settings()
    table = get_table(settings.volunteers_table)
    resp = table.get_item(Key={"id": volunteer_id})
    return cast("dict[str, Any] | None", resp.get("Item"))


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
        ExpressionAttributeValues=_encode_item(expr_values),
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
    return cast("list[dict[str, Any]]", resp.get("Items", []))


# ── Recipient Requests ─────────────────────────────────────────────────────


def create_recipient_request(request: dict) -> dict:
    """Insert a new recipient request."""
    settings = get_settings()
    table = get_table(settings.recipients_table)
    record = {**request, "created_at": _now_iso()}
    table.put_item(Item=_encode_item(record))
    return record


def get_recipient_request(request_id: str) -> dict | None:
    """Get a single recipient request by ID."""
    settings = get_settings()
    table = get_table(settings.recipients_table)
    resp = table.get_item(Key={"id": request_id})
    return cast("dict[str, Any] | None", resp.get("Item"))


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
        ExpressionAttributeValues=_encode_item(expr_values),
    )
    return get_recipient_request(request_id)


def delete_recipient_request(request_id: str) -> bool:
    """Delete a recipient request.

    Used by the right-to-delete endpoint; callers should record a separate
    audit entry capturing the deletion request.
    """
    settings = get_settings()
    table = get_table(settings.recipients_table)
    resp = table.delete_item(Key={"id": request_id}, ReturnValues="ALL_OLD")
    return "Attributes" in resp


def list_recipient_requests(resolved: bool | None = None, limit: int = 50) -> list[dict]:
    """List recipient requests, optionally filtered by resolved status.

    Uses a scan + filter expression: DynamoDB does not allow BOOLEAN
    partition keys, so `resolved` cannot be an indexed query.
    """
    settings = get_settings()
    table = get_table(settings.recipients_table)
    if resolved is not None:
        from boto3.dynamodb.conditions import Attr

        resp = table.scan(
            FilterExpression=Attr("resolved").eq(bool(resolved)),
            Limit=limit,
        )
    else:
        resp = table.scan(Limit=limit)
    return cast("list[dict[str, Any]]", resp.get("Items", []))


# ── Shifts ─────────────────────────────────────────────────────────────────


def create_shift(shift: dict) -> dict:
    """Insert a new shift record."""
    settings = get_settings()
    table = get_table(settings.shifts_table)
    record = {**shift, "created_at": _now_iso()}
    table.put_item(Item=_encode_item(record))
    return record


def get_shift(shift_id: str) -> dict | None:
    """Get a single shift by ID."""
    settings = get_settings()
    table = get_table(settings.shifts_table)
    resp = table.get_item(Key={"id": shift_id})
    return cast("dict[str, Any] | None", resp.get("Item"))


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
        ExpressionAttributeValues=_encode_item(expr_values),
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
    return cast("list[dict[str, Any]]", items)


# ── Events ─────────────────────────────────────────────────────────────────


def create_event(event: dict) -> dict:
    """Insert a new event record.

    Events carry ``created_at`` as their sort key (see the infra stack); the
    ``id`` is generated when the caller does not provide one.
    """
    settings = get_settings()
    table = get_table(settings.events_table)
    record = {**event, "id": event.get("id", str(uuid.uuid4())), "created_at": _now_iso()}
    table.put_item(Item=_encode_item(record))
    return record


def list_events(limit: int = 50) -> list[dict]:
    """List recent events, newest first."""
    settings = get_settings()
    table = get_table(settings.events_table)
    resp = table.scan(Limit=limit)
    items = resp.get("Items", [])
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return cast("list[dict[str, Any]]", items[:limit])


# ── Audit Trail ────────────────────────────────────────────────────────────


def create_audit_entry(entry: dict) -> dict:
    """Insert an audit trail entry.

    Generates the ``id`` partition key (required by the provisioned table) when
    the caller does not supply one, and stamps the ``timestamp`` sort key.
    """
    settings = get_settings()
    table = get_table(settings.audit_table)
    record = {
        **entry,
        "id": entry.get("id", str(uuid.uuid4())),
        "timestamp": _now_iso(),
    }
    table.put_item(Item=_encode_item(record))
    return record


def list_audit_entries(limit: int = 50) -> list[dict]:
    """List recent audit entries, newest first."""
    settings = get_settings()
    table = get_table(settings.audit_table)
    resp = table.scan(Limit=limit)
    items = resp.get("Items", [])
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return cast("list[dict[str, Any]]", items[:limit])


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
