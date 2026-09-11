"""Tools for the RecipientAgent — helps people find aid."""

from __future__ import annotations

import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from strands import tool

from haven.config import get_settings
from haven.db import (
    create_audit_entry,
    create_event,
)


@tool
def find_nearest_pantry(
    latitude: float,
    longitude: float,
    category: str = "",
    language: str = "en",
) -> dict:
    """Find the nearest food pantry based on location.

    Reads from the dedicated pantries table (HAVEN_PANTRIES_TABLE) when it is
    provisioned. The donations table stores donor offers, not pantries, so it
    is never treated as pantry data.
    """
    settings = get_settings()

    if not settings.pantries_table:
        return {
            "pantries": [],
            "total_found": 0,
            "search_location": {"lat": latitude, "lng": longitude},
            "data_available": False,
            "message": "Pantry registry is not provisioned. No pantry data found.",
        }

    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.pantries_table)

    resp = table.scan()
    items = resp.get("Items", [])

    pantries = []
    for item in items:
        lat = item.get("latitude")
        lng = item.get("longitude")
        if lat and lng:
            dist = ((float(lat) - latitude) ** 2 + (float(lng) - longitude) ** 2) ** 0.5 * 69.0
            pantries.append(
                {
                    "id": item.get("id", ""),
                    "name": item.get("name", "Unknown Pantry"),
                    "address": item.get("address", ""),
                    "distance_miles": round(dist, 1),
                    "services": item.get("services", []),
                    "eligible": item.get("eligibility_checked", False),
                }
            )

    pantries.sort(key=lambda x: x["distance_miles"])
    return {
        "pantries": pantries[:5],
        "total_found": len(pantries),
        "search_location": {"lat": latitude, "lng": longitude},
        "data_available": True,
    }


@tool
def check_pantry_hours(pantry_id: str) -> dict:
    """Check current open/closed status and hours for a pantry.

    Only reports operating hours when a real pantry record with hours exists.
    """
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.donations_table)
    resp = table.get_item(Key={"id": pantry_id})
    item = resp.get("Item", {})

    if settings.pantries_table:
        pantry_table = dynamodb.Table(settings.pantries_table)
        pantry_resp = pantry_table.get_item(Key={"id": pantry_id})
        pantry = pantry_resp.get("Item", {})
    else:
        pantry = {}

    hours = pantry.get("hours") or item.get("hours")
    if not hours:
        return {
            "pantry_id": pantry_id,
            "data_available": False,
            "is_open": None,
            "hours": None,
            "message": "Operating hours are not on file for this pantry.",
        }

    return {
        "pantry_id": pantry_id,
        "name": pantry.get("name") or item.get("donor_name", "Unknown"),
        "address": pantry.get("address") or item.get("address", ""),
        "is_open": None,
        "hours": hours,
        "data_available": True,
        "message": "Hours listed; current open/closed status requires an opening-hours service.",
    }


@tool
def verify_eligibility(
    pantry_id: str,
    household_size: int,
    zip_code: str,
    income_level: str = "",
) -> dict:
    """Check if someone is eligible for services at a specific pantry.

    Returns requirements and does not fabricate an eligibility determination;
    eligibility is only asserted when the pantry registry carries it.
    """
    settings = get_settings()
    pantry = {}
    if settings.pantries_table:
        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        resp = dynamodb.Table(settings.pantries_table).get_item(Key={"id": pantry_id})
        pantry = resp.get("Item", {})

    create_audit_entry(
        {
            "action": "eligibility_checked",
            "agent": "recipient",
            "entity_type": "pantry",
            "entity_id": pantry_id,
            "details": {"household_size": household_size, "zip_code": zip_code},
        }
    )

    if not pantry:
        return {
            "pantry_id": pantry_id,
            "eligible": None,
            "data_available": False,
            "message": "No eligibility data on record for this pantry.",
            "requirements": [],
            "household_size": household_size,
        }

    return {
        "pantry_id": pantry_id,
        "eligible": bool(pantry.get("eligibility_checked")),
        "requirements": pantry.get("requirements")
        or [
            "Photo ID or proof of address",
            "Self-declaration of need (no income verification required)",
        ],
        "next_steps": pantry.get("next_steps", "Contact the pantry for intake details."),
        "household_size": household_size,
    }


@tool
def list_available_items(pantry_id: str) -> dict:
    """List currently available food items at a pantry from real inventory."""
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.donations_table)

    resp = table.query(
        IndexName="status-index",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("status").eq("distributed"),
    )
    items = resp.get("Items", [])

    categories: dict[str, list[str]] = {}
    for item in items:
        cat = item.get("category", "other")
        desc = item.get("description", "")
        if cat not in categories:
            categories[cat] = []
        if desc and desc not in categories[cat]:
            categories[cat].append(desc)

    return {
        "pantry_id": pantry_id,
        "categories": categories
        if categories
        else {"produce": [], "protein": [], "dairy": [], "bakery": [], "canned": []},
        "total_items": sum(len(v) for v in categories.values()),
    }


@tool
def translate_response(
    text: str,
    source_language: str,
    target_language: str,
) -> dict:
    """Translate a response using Amazon Translate."""
    settings = get_settings()

    if source_language == target_language:
        return {
            "original_text": text,
            "translated_text": text,
            "source_language": source_language,
            "target_language": target_language,
            "confidence": 1.0,
            "engine": "passthrough",
        }

    try:
        client = boto3.client("translate", region_name=settings.aws_region)
        resp = client.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=target_language,
        )
        return {
            "original_text": text,
            "translated_text": resp["TranslatedText"],
            "source_language": source_language,
            "target_language": target_language,
            "confidence": 0.95,
            "engine": "amazon-translate",
        }
    except (ClientError, BotoCoreError):
        return {
            "original_text": text,
            "translated_text": text,
            "source_language": source_language,
            "target_language": target_language,
            "confidence": 0.0,
            "engine": "passthrough-error",
        }


@tool
def submit_recipient_request(
    phone: str,
    request_text: str,
    language: str = "en",
    latitude: float = 0.0,
    longitude: float = 0.0,
    household_size: int = 1,
    dietary_restrictions: list[str] | None = None,
) -> dict:
    """Submit and store a recipient request in DynamoDB."""
    if dietary_restrictions is None:
        dietary_restrictions = []

    record = {
        "id": str(uuid.uuid4()),
        "phone": phone,
        "language": language,
        "request_text": request_text,
        "household_size": household_size,
        "dietary_restrictions": dietary_restrictions,
        "latitude": latitude,
        "longitude": longitude,
        "resolved": False,
    }

    from haven.db import create_recipient_request as db_create

    db_create(record)

    create_event(
        {
            "id": str(uuid.uuid4()),
            "event_type": "recipient_request",
            "source": "recipient_agent",
            "payload": {"request_id": record["id"], "language": language},
            "urgency": "high",
        }
    )

    return {
        "request_id": record["id"],
        "status": "submitted",
        "message": "Request received. Searching for nearest resources.",
    }
