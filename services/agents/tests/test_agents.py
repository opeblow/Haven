"""Tests for the Haven agents (unit tests, no real LLM calls)."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestSupervisor:
    @pytest.fixture
    def supervisor(self, mock_dynamodb):
        with patch("haven.agents.supervisor.Agent"):
            from haven.agents.supervisor import Supervisor

            s = Supervisor()
            return s

    def test_parse_routing_decision_single_agent(self, supervisor):
        result = supervisor._parse_routing_decision("donor")
        assert result == ["donor"]

    def test_parse_routing_decision_multiple_agents(self, supervisor):
        result = supervisor._parse_routing_decision("donor and logistics")
        assert "donor" in result
        assert "logistics" in result

    def test_parse_routing_decision_prose(self, supervisor):
        result = supervisor._parse_routing_decision("I'll route this to the volunteer agent for matching.")
        assert "volunteer" in result

    def test_parse_routing_decision_fallback(self, supervisor):
        result = supervisor._parse_routing_decision("unknown response with no agents")
        assert result == ["donor", "compliance"]

    def test_parse_routing_decision_all_agents(self, supervisor):
        result = supervisor._parse_routing_decision("donor, volunteer, recipient, logistics, compliance")
        assert len(result) == 5

    def test_get_status(self, supervisor):
        import asyncio

        status = asyncio.run(supervisor.get_status())
        assert status["supervisor"] == "active"
        assert status["uptime"] == "operational"
        assert len(status["agents"]) == 5
