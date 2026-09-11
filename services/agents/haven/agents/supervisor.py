"""Supervisor — orchestrates the Haven agent swarm."""

from __future__ import annotations

import json
from typing import Any

import structlog
from strands import Agent

from haven.agents.compliance_agent import create_compliance_agent
from haven.agents.donor_agent import create_donor_agent
from haven.agents.logistics_agent import create_logistics_agent
from haven.agents.recipient_agent import create_recipient_agent
from haven.agents.volunteer_agent import create_volunteer_agent
from haven.config import get_settings
from haven.models import AgentEvent, UrgencyLevel

logger = structlog.get_logger()

SUPERVISOR_SYSTEM_PROMPT = """You are the Haven Supervisor, the orchestrator of a
multi-agent system that manages food bank operations.

You coordinate 5 specialized agents:
1. DONOR AGENT — handles donation offers, donor communication, tax receipts
2. VOLUNTEER AGENT — matches volunteers to shifts, manages engagement
3. RECIPIENT AGENT — helps people find food and resources, multi-language
4. LOGISTICS AGENT — routes food, manages cold chain, dispatches drivers
5. COMPLIANCE AGENT — generates reports, maintains audit trails

Your job is to:
- Route incoming events to the right agent(s)
- Coordinate multi-agent workflows (e.g., a new donation triggers logistics + compliance)
- Escalate to humans when needed (unusual situations, high-value decisions, complaints)
- Track which agents have processed each event
- Maintain context across the entire workflow

Escalation rules (ALWAYS escalate to human):
- Donation value > $5,000
- Food safety incident
- Volunteer safety concern
- Recipient complaint
- Agent unsure or conflicting recommendations
- System error or tool failure

For each event, determine which agent(s) should handle it and why.
Explain your routing decision briefly."""


class Supervisor:
    """Orchestrates the Haven agent swarm."""

    def __init__(self) -> None:
        settings = get_settings()
        self._agent = Agent(
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
            model=settings.bedrock_model_id,
        )
        self._donor_agent = create_donor_agent()
        self._volunteer_agent = create_volunteer_agent()
        self._recipient_agent = create_recipient_agent()
        self._logistics_agent = create_logistics_agent()
        self._compliance_agent = create_compliance_agent()
        self._agents = {
            "donor": self._donor_agent,
            "volunteer": self._volunteer_agent,
            "recipient": self._recipient_agent,
            "logistics": self._logistics_agent,
            "compliance": self._compliance_agent,
        }
        logger.info("haven.supervisor.initialized")

    async def route_event(self, event: AgentEvent) -> dict[str, Any]:
        """Route an incoming event to the appropriate agent(s).

        The supervisor analyzes the event, determines which agent(s)
        should handle it, and coordinates the response.
        """
        logger.info(
            "haven.supervisor.routing",
            event_type=event.event_type,
            urgency=event.urgency.value,
        )

        routing_decision = await self._agent.invoke(
            f"Route this event to the appropriate agent(s). "
            f"Event type: {event.event_type}\n"
            f"Source: {event.source}\n"
            f"Payload: {json.dumps(event.payload, default=str)}\n"
            f"Urgency: {event.urgency.value}\n"
            f"Already processed by: {event.processed_by}\n\n"
            f"Which agent(s) should handle this? Return agent names as a comma-separated list."
        )

        target_agents = self._parse_routing_decision(str(routing_decision))

        results = {}
        for agent_name in target_agents:
            if agent_name in self._agents:
                logger.info(
                    "haven.supervisor.delegate",
                    agent=agent_name,
                    event_type=event.event_type,
                )
                response = await self._agents[agent_name].invoke(
                    f"Handle this event:\n{json.dumps(event.payload, default=str)}"
                )
                results[agent_name] = str(response)
                event.processed_by.append(agent_name)

        should_escalate = event.urgency in (UrgencyLevel.HIGH, UrgencyLevel.CRITICAL)

        return {
            "event_id": event.id,
            "routing_decision": target_agents,
            "results": results,
            "escalated_to_human": should_escalate,
            "all_processed": len(event.processed_by) > 0,
        }

    async def handle_donation_offer(self, donor_data: dict) -> dict[str, Any]:
        """End-to-end workflow for a new donation offer."""
        event = AgentEvent(
            event_type="donation_offer",
            source=donor_data.get("source", "sms"),
            payload=donor_data,
            urgency=(
                UrgencyLevel.HIGH
                if donor_data.get("requires_refrigeration")
                else UrgencyLevel.MEDIUM
            ),
        )
        result = await self.route_event(event)

        if result.get("all_processed"):
            logistics_event = AgentEvent(
                event_type="logistics_planning",
                source="supervisor",
                payload={
                    "donation_id": donor_data.get("id", ""),
                    "origin": donor_data.get("address", ""),
                    "cold_chain": donor_data.get("requires_refrigeration", False),
                },
            )
            logistics_result = await self._logistics_agent.invoke(
                f"Plan logistics for this donation:\n{json.dumps(logistics_event.payload, default=str)}"
            )
            result["logistics"] = str(logistics_result)

        return result

    async def handle_volunteer_inquiry(self, volunteer_data: dict) -> dict[str, Any]:
        """Handle a volunteer wanting to sign up or check shifts."""
        event = AgentEvent(
            event_type="volunteer_inquiry",
            source="web",
            payload=volunteer_data,
        )
        return await self.route_event(event)

    async def handle_recipient_request(self, request_data: dict) -> dict[str, Any]:
        """Handle someone seeking aid."""
        event = AgentEvent(
            event_type="recipient_request",
            source=request_data.get("source", "sms"),
            payload=request_data,
            urgency=UrgencyLevel.HIGH,
        )
        return await self.route_event(event)

    async def get_status(self) -> dict[str, Any]:
        """Return the current status of all agents."""
        return {
            "supervisor": "active",
            "agents": {
                name: {"status": "active", "model": get_settings().bedrock_model_id}
                for name in self._agents
            },
            "uptime": "operational",
        }

    def _parse_routing_decision(self, decision: str) -> list[str]:
        """Parse agent names from supervisor's routing decision."""
        known_agents = {"donor", "volunteer", "recipient", "logistics", "compliance"}
        words = decision.lower().replace(",", " ").split()
        return [w for w in words if w in known_agents] or ["donor", "compliance"]
