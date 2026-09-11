"""Moto-backed integration tests for Haven DynamoDB helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

from haven.config import Settings
from haven.db import (
    _encode_item,
    _extract_pounds,
    create_audit_entry,
    create_donation,
    create_event,
    create_recipient_request,
    delete_recipient_request,
    get_donation,
    get_donation_stats,
    get_recipient_request,
    list_recipient_requests,
)

TABLE_NAMES = {
    "donations": "haven-donations",
    "volunteers": "haven-volunteers",
    "recipients": "haven-recipients",
    "shifts": "haven-shifts",
    "events": "haven-events",
    "audit": "haven-audit",
}


def _create_table(dynamodb_resource, name: str, pk: str = "id", global_indexes=None):
    attrs = [{"AttributeName": pk, "AttributeType": "S"}]
    key_schema = [{"AttributeName": pk, "KeyType": "HASH"}]
    kwargs: dict = {
        "TableName": name,
        "KeySchema": key_schema,
        "AttributeDefinitions": attrs,
        "BillingMode": "PAY_PER_REQUEST",
    }
    gsis = []
    for gsi in global_indexes or []:
        gsis.append(
            {
                "IndexName": gsi["IndexName"],
                "KeySchema": [{"AttributeName": gsi["KeySchema"], "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        )
        attrs.append({"AttributeName": gsi["KeySchema"], "AttributeType": "S"})
    if gsis:
        kwargs["GlobalSecondaryIndexes"] = gsis
    dynamodb_resource.create_table(**kwargs)


@pytest.fixture(autouse=True)
def setup_tables(monkeypatch):
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        _create_table(
            resource, TABLE_NAMES["donations"], global_indexes=[{"IndexName": "status-index", "KeySchema": "status"}]
        )
        _create_table(
            resource, TABLE_NAMES["volunteers"], global_indexes=[{"IndexName": "status-index", "KeySchema": "status"}]
        )
        _create_table(resource, TABLE_NAMES["recipients"])
        _create_table(
            resource, TABLE_NAMES["shifts"], global_indexes=[{"IndexName": "status-index", "KeySchema": "status"}]
        )
        _create_table(resource, TABLE_NAMES["events"])
        _create_table(resource, TABLE_NAMES["audit"])

        settings = Settings(
            aws_region="us-east-1",
            donations_table=TABLE_NAMES["donations"],
            volunteers_table=TABLE_NAMES["volunteers"],
            recipients_table=TABLE_NAMES["recipients"],
            shifts_table=TABLE_NAMES["shifts"],
            events_table=TABLE_NAMES["events"],
            audit_table=TABLE_NAMES["audit"],
            pantries_table="",
        )
        monkeypatch.setattr("haven.db.get_settings", lambda: settings)
        yield resource


class TestEncodeItem:
    def test_float_to_decimal(self):
        encoded = _encode_item({"amount": 1.25})
        assert isinstance(encoded["amount"], Decimal)
        assert encoded["amount"] == Decimal("1.25")

    def test_datetime_to_iso(self):
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        encoded = _encode_item({"created_at": ts})
        assert encoded["created_at"] == "2026-01-01T00:00:00+00:00"

    def test_nested_recursive(self):
        encoded = _encode_item({"a": {"b": [1.5, {"c": 2.5}]}})
        assert isinstance(encoded["a"]["b"][0], Decimal)
        assert isinstance(encoded["a"]["b"][1]["c"], Decimal)

    def test_strings_pass_through(self):
        encoded = _encode_item({"name": "hello"})
        assert encoded["name"] == "hello"


class TestExtractPounds:
    def test_explicit_lbs(self):
        assert _extract_pounds("50 lbs") == 50.0
        assert _extract_pounds("100.5 pound") == 100.5
        assert _extract_pounds("25lb") == 25.0

    def test_no_explicit_unit_returns_none(self):
        assert _extract_pounds("5 boxes") is None
        assert _extract_pounds("large bag") is None

    def test_empty_returns_none(self):
        assert _extract_pounds("") is None


class TestDonations:
    def test_create_donation_encodes_float(self, setup_tables):
        donation = create_donation(
            {
                "id": str(uuid.uuid4()),
                "donor_name": "Test Farm",
                "quantity": "50 lbs",
                "estimated_weight_lbs": 50.0,
                "status": "offered",
            }
        )
        assert donation["estimated_weight_lbs"] == 50.0
        real = get_donation(donation["id"])
        assert real is not None
        assert isinstance(real.get("estimated_weight_lbs"), (int, float, Decimal))


class TestAudit:
    def test_id_and_timestamp_auto_generated(self, setup_tables):
        entry = create_audit_entry(
            {
                "action": "test",
                "agent": "unit",
                "entity_type": "donation",
                "entity_id": "x",
            }
        )
        assert entry["id"]
        assert entry["timestamp"]


class TestEvents:
    def test_created_at_and_id_populated(self, setup_tables):
        evt = create_event(
            {
                "event_type": "test",
                "source": "unit",
            }
        )
        assert evt["id"]
        assert evt["created_at"]


class TestRecipients:
    def test_lifecycle(self, setup_tables):
        rid = str(uuid.uuid4())
        create_recipient_request(
            {
                "id": rid,
                "phone": "555-1234",
                "request_text": "Need food",
                "resolved": False,
            }
        )
        item = get_recipient_request(rid)
        assert item is not None
        assert item["resolved"] is False

        all_items = list_recipient_requests(resolved=False)
        assert any(i["id"] == rid for i in all_items)

        resolved_items = list_recipient_requests(resolved=True)
        assert not any(i["id"] == rid for i in resolved_items)

        deleted = delete_recipient_request(rid)
        assert deleted is True
        assert get_recipient_request(rid) is None
        assert delete_recipient_request(rid) is False


class TestDonationStats:
    def test_only_explicit_lbs_counted(self, setup_tables):
        create_donation({"id": "d1", "quantity": "50 lbs", "status": "distributed"})
        create_donation({"id": "d2", "quantity": "10 boxes", "status": "offered"})
        stats = get_donation_stats()
        assert stats["total_lbs"] == 50.0
        assert stats["total_donations"] == 2
