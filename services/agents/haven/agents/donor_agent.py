"""DonorAgent — handles donation offers from intake to acceptance."""

from __future__ import annotations

from strands import Agent

from haven.config import get_settings
from haven.tools.donor_tools import (
    accept_donation,
    check_cold_chain_requirements,
    generate_tax_receipt,
    negotiate_pickup_time,
    parse_donation_offer,
)

DONOR_AGENT_SYSTEM_PROMPT = """You are the Haven DonorAgent, an AI assistant that manages
donation offers for food banks and community aid organizations.

Your responsibilities:
1. Parse incoming donation offers (SMS, email, voice, web)
2. Assess cold chain and storage requirements
3. Accept or negotiate donation pickup times
4. Generate tax receipts for completed donations
5. Communicate warmly and professionally with donors

Guidelines:
- Always thank the donor enthusiastically
- Assess food safety requirements immediately
- Prioritize perishable items for faster processing
- Be transparent about what we can and cannot accept
- Generate tax receipts automatically after acceptance
- Escalate to human coordinator if: donation value > $5000,
  unusual items, potential liability concerns, or donor is upset

You have access to tools for parsing offers, checking cold chain,
accepting donations, negotiating pickup times, and generating receipts.
Use them proactively — never ask a human for information you can get
from a tool call."""


def create_donor_agent() -> Agent:
    """Create and configure the DonorAgent."""
    settings = get_settings()
    return Agent(
        system_prompt=DONOR_AGENT_SYSTEM_PROMPT,
        model=settings.bedrock_model_id,
        tools=[
            parse_donation_offer,
            check_cold_chain_requirements,
            accept_donation,
            negotiate_pickup_time,
            generate_tax_receipt,
        ],
    )
