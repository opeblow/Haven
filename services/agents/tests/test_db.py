"""Tests for Haven database layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestDonationDB:
    def test_create_donation(self, mock_dynamodb):
        from haven.db import create_donation

        _, mock_table = mock_dynamodb
        result = create_donation({
            "id": "don-001",
            "donor_name": "Green Farms",
            "category": "produce",
        })

        assert mock_table.put_item.called
        assert result["donor_name"] == "Green Farms"
        assert result["created_at"] is not None

    def test_get_donation(self, mock_dynamodb):
        from haven.db import get_donation

        _, mock_table = mock_dynamodb
        mock_table.get_item.return_value = {"Item": {"id": "don-001", "status": "offered"}}

        result = get_donation("don-001")
        assert result is not None
        assert result["id"] == "don-001"

    def test_get_donation_not_found(self, mock_dynamodb):
        from haven.db import get_donation

        _, mock_table = mock_dynamodb
        mock_table.get_item.return_value = {}

        result = get_donation("nonexistent")
        assert result is None

    def test_update_donation(self, mock_dynamodb):
        from haven.db import update_donation

        _, mock_table = mock_dynamodb
        mock_table.get_item.return_value = {"Item": {"id": "don-001", "status": "accepted"}}

        result = update_donation("don-001", {"status": "in_transit"})
        assert mock_table.update_item.called
        assert result["status"] == "in_transit"

    def test_list_donations_all(self, mock_dynamodb):
        from haven.db import list_donations

        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": [{"id": "1"}, {"id": "2"}]}

        result = list_donations()
        assert len(result) == 2

    def test_list_donations_by_status(self, mock_dynamodb):
        from haven.db import list_donations

        _, mock_table = mock_dynamodb
        mock_table.query.return_value = {"Items": [{"id": "1", "status": "accepted"}]}

        result = list_donations(status="accepted")
        assert len(result) == 1
        mock_table.query.assert_called_once()


class TestVolunteerDB:
    def test_create_volunteer(self, mock_dynamodb):
        from haven.db import create_volunteer

        _, mock_table = mock_dynamodb
        result = create_volunteer({"id": "v-001", "name": "Maria"})

        assert mock_table.put_item.called
        assert result["name"] == "Maria"

    def test_list_volunteers(self, mock_dynamodb):
        from haven.db import list_volunteers

        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": [{"id": "v1"}, {"id": "v2"}]}

        result = list_volunteers()
        assert len(result) == 2


class TestEventDB:
    def test_create_event(self, mock_dynamodb):
        from haven.db import create_event

        _, mock_table = mock_dynamodb
        result = create_event({
            "id": "evt-001",
            "event_type": "donation_offer",
            "source": "donor_agent",
        })

        assert mock_table.put_item.called
        assert result["event_type"] == "donation_offer"

    def test_list_events(self, mock_dynamodb):
        from haven.db import list_events

        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": [{"id": "1", "created_at": "2026-09-10"}, {"id": "2", "created_at": "2026-09-11"}]}

        result = list_events()
        assert len(result) == 2
        assert result[0]["created_at"] == "2026-09-11"


class TestAuditDB:
    def test_create_audit_entry(self, mock_dynamodb):
        from haven.db import create_audit_entry

        _, mock_table = mock_dynamodb
        result = create_audit_entry({
            "action": "donation_accepted",
            "agent": "donor",
            "entity_type": "donation",
            "entity_id": "don-001",
        })

        assert mock_table.put_item.called
        assert result["action"] == "donation_accepted"
        assert result["timestamp"] is not None

    def test_list_audit_entries(self, mock_dynamodb):
        from haven.db import list_audit_entries

        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": [{"action": "a1"}, {"action": "a2"}]}

        result = list_audit_entries(limit=10)
        assert len(result) == 2


class TestDashboardStats:
    def test_get_dashboard_stats_aggregates(self, mock_dynamodb):
        from haven.db import get_dashboard_stats

        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {
            "Items": [
                {"id": "d1", "status": "distributed", "quantity": "100 lbs"},
                {"id": "v1", "status": "available"},
                {"id": "s1", "status": "open"},
                {"id": "r1", "resolved": True},
            ]
        }

        result = get_dashboard_stats()
        assert "total_donations" in result
        assert "active_volunteers" in result
        assert "open_shifts" in result
