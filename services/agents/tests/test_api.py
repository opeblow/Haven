"""Tests for Haven API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(mock_dynamodb):
    """Create a test client with mocked dependencies."""
    with patch("haven.api.Supervisor") as mock_supervisor_cls:
        mock_supervisor = MagicMock()
        mock_supervisor.get_status = AsyncMock(
            return_value={
                "supervisor": "active",
                "agents": {},
                "uptime": "operational",
            }
        )
        mock_supervisor.handle_donation_offer = AsyncMock(
            return_value={
                "event_id": "test-event",
                "routing_decision": ["donor"],
                "results": {"donor": "processed"},
                "escalated_to_human": False,
                "all_processed": True,
            }
        )
        mock_supervisor.handle_volunteer_inquiry = AsyncMock(
            return_value={
                "event_id": "test-event",
                "routing_decision": ["volunteer"],
                "results": {"volunteer": "processed"},
                "escalated_to_human": False,
                "all_processed": True,
            }
        )
        mock_supervisor.handle_recipient_request = AsyncMock(
            return_value={
                "event_id": "test-event",
                "routing_decision": ["recipient"],
                "results": {"recipient": "processed"},
                "escalated_to_human": True,
                "all_processed": True,
            }
        )
        mock_supervisor_cls.return_value = mock_supervisor

        from haven.api import app

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c, mock_supervisor


class TestHealthEndpoint:
    def test_health_check(self, client):
        c, _ = client
        resp = c.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "haven-agents"
        assert data["supervisor"] == "active"


class TestDonationEndpoints:
    def test_submit_donation_offer(self, client):
        c, mock_supervisor = client
        resp = c.post(
            "/api/donations/offer",
            json={
                "donor_name": "Green Farms",
                "donor_phone": "555-0100",
                "description": "Fresh vegetables",
                "quantity": "200 lbs",
                "category": "produce",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        mock_supervisor.handle_donation_offer.assert_called_once()

    def test_list_donations_empty(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": []}
        resp = c.get("/api/donations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["donations"] == []
        assert data["total"] == 0

    def test_list_donations_with_status_filter(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.query.return_value = {"Items": [{"id": "1", "status": "accepted"}]}
        resp = c.get("/api/donations?status=accepted")
        assert resp.status_code == 200

    def test_get_donation_not_found(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.get_item.return_value = {}
        resp = c.get("/api/donations/nonexistent")
        assert resp.status_code == 404


class TestVolunteerEndpoints:
    def test_submit_volunteer_inquiry(self, client, mock_dynamodb):
        c, mock_supervisor = client
        resp = c.post(
            "/api/volunteers/inquiry",
            json={
                "name": "Maria Rodriguez",
                "phone": "555-0123",
                "email": "maria@test.com",
                "skills": ["food_distribution"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "volunteer_id" in data
        mock_supervisor.handle_volunteer_inquiry.assert_called_once()

    def test_list_volunteers(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": [{"id": "v1", "name": "Test"}]}
        resp = c.get("/api/volunteers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1


class TestRecipientEndpoints:
    def test_submit_recipient_request(self, client):
        c, mock_supervisor = client
        resp = c.post(
            "/api/recipients/request",
            json={
                "phone": "555-0789",
                "request_text": "Need food for family",
                "language": "en",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        mock_supervisor.handle_recipient_request.assert_called_once()

    def test_list_recipients(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": []}
        resp = c.get("/api/recipients")
        assert resp.status_code == 200


class TestEventFeed:
    def test_get_event_feed(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": [{"id": "e1", "event_type": "test"}]}
        resp = c.get("/api/events/feed")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data


class TestStats:
    def test_get_stats(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": []}
        resp = c.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_donations" in data
        assert "active_volunteers" in data


class TestShiftEndpoints:
    def test_list_shifts(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": []}
        resp = c.get("/api/shifts")
        assert resp.status_code == 200

    def test_create_shift(self, client, mock_dynamodb):
        c, _ = client
        resp = c.post(
            "/api/shifts",
            json={
                "pantry_id": "p1",
                "pantry_name": "Test Pantry",
                "role": "food_distribution",
                "start_time": "2026-09-12T09:00:00Z",
                "end_time": "2026-09-12T13:00:00Z",
                "volunteers_needed": 3,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True


class TestAuditEndpoint:
    def test_get_audit_log(self, client, mock_dynamodb):
        c, _ = client
        _, mock_table = mock_dynamodb
        mock_table.scan.return_value = {"Items": [{"action": "test"}]}
        resp = c.get("/api/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
