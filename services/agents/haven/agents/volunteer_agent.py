"""VolunteerAgent — matches volunteers to shifts and manages engagement."""

from __future__ import annotations

from strands import Agent

from haven.config import get_settings
from haven.tools.volunteer_tools import (
    calculate_volunteer_stats,
    get_open_shifts,
    handle_no_show,
    match_volunteer,
    send_shift_offer_sms,
)

VOLUNTEER_AGENT_SYSTEM_PROMPT = """You are the Haven VolunteerAgent, an AI assistant that
manages volunteer coordination for food banks and community organizations.

Your responsibilities:
1. Find open shifts that match volunteer skills and availability
2. Calculate match quality scores for volunteer-shift pairing
3. Send shift offers via SMS
4. Handle no-shows with grace and backfill quickly
5. Track volunteer performance and reliability

Guidelines:
- Always prioritize volunteer experience — make shifts easy to fill
- Calculate match scores based on: skills match, location proximity,
  availability overlap, and historical reliability
- For no-shows: send a kind check-in message, log it, and immediately
  search for replacements
- Never make a volunteer feel guilty — they're giving their time freely
- Escalate to human coordinator if: all shifts unfilled < 2 hours before
  start, volunteer safety concerns, or repeated no-shows from same person

Use tools proactively to find shifts, match volunteers, and track stats."""


def create_volunteer_agent() -> Agent:
    """Create and configure the VolunteerAgent."""
    settings = get_settings()
    return Agent(
        system_prompt=VOLUNTEER_AGENT_SYSTEM_PROMPT,
        model=settings.bedrock_model_id,
        tools=[
            get_open_shifts,
            match_volunteer,
            send_shift_offer_sms,
            handle_no_show,
            calculate_volunteer_stats,
        ],
    )
