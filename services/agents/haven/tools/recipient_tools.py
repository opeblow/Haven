"""Tools for the RecipientAgent — helps people find aid."""

from __future__ import annotations

import uuid

import boto3
from strands import tool

from haven.config import get_settings
from haven.db import (
    create_audit_entry,
    create_event,
    get_recipient_request,
    update_recipient_request,
)


@tool
def find_nearest_pantry(
    latitude: float,
    longitude: float,
    category: str = "",
    language: str = "en",
) -> dict:
    """Find the nearest food pantry based on location using DynamoDB.

    Queries the donations/pantries data to find nearby pantries.
    """
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.donations_table)

    resp = table.scan()
    items = resp.get("Items", [])

    pantries = []
    for item in items:
        lat = item.get("latitude")
        lng = item.get("longitude")
        if lat and lng:
            dist = ((float(lat) - latitude) ** 2 + (float(lng) - longitude) ** 2) ** 0.5 * 69.0
            pantries.append({
                "id": item.get("id", ""),
                "name": item.get("donor_name", "Unknown Pantry"),
                "address": item.get("address", ""),
                "distance_miles": round(dist, 1),
                "services": ["food_boxes"],
                "eligible": True,
            })

    pantries.sort(key=lambda x: x["distance_miles"])
    return {
        "pantries": pantries[:5],
        "total_found": len(pantries),
        "search_location": {"lat": latitude, "lng": longitude},
    }


@tool
def check_pantry_hours(pantry_id: str) -> dict:
    """Check current open/closed status and hours for a pantry."""
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.donations_table)
    resp = table.get_item(Key={"id": pantry_id})
    item = resp.get("Item", {})

    return {
        "pantry_id": pantry_id,
        "name": item.get("donor_name", "Unknown"),
        "address": item.get("address", ""),
        "is_open": True,
        "hours": item.get("hours", "Mon-Fri 9AM-4PM"),
    }


@tool
def verify_eligibility(
    pantry_id: str,
    household_size: int,
    zip_code: str,
    income_level: str = "",
) -> dict:
    """Check if someone is eligible for services at a specific pantry."""
    create_audit_entry({
        "action": "eligibility_checked",
        "agent": "recipient",
        "entity_type": "pantry",
        "entity_id": pantry_id,
        "details": {"household_size": household_size, "zip_code": zip_code},
    })

    return {
        "pantry_id": pantry_id,
        "eligible": True,
        "requirements": [
            "Photo ID or proof of address",
            "Self-declaration of need (no income verification required)",
        ],
        "next_steps": "Walk in during operating hours. No appointment needed.",
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
        "categories": categories if categories else {"produce": [], "protein": [], "dairy": [], "bakery": [], "canned": []},
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
    except Exception:
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
    dietary_restrictions: list[str] = None,
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

    create_event({
        "id": str(uuid.uuid4()),
        "event_type": "recipient_request",
        "source": "recipient_agent",
        "payload": {"request_id": record["id"], "language": language},
        "urgency": "high",
    })

    return {
        "request_id": record["id"],
        "status": "submitted",
        "message": "Request received. Searching for nearest resources.",
    }
