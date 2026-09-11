# Haven Agent Guide

## Overview

Haven uses a multi-agent architecture with 5 specialized agents coordinated by a Supervisor. Each agent is built with the Strands Agents SDK and has domain-specific tools.

## The Swarm

### Supervisor
- **Role**: Orchestrator — routes events to the right agent(s)
- **Model**: Nova Micro (fast routing)
- **Responsibilities**: Event routing, multi-agent coordination, human escalation

### Donor Agent
- **Role**: Handles donation offers from intake to acceptance
- **Model**: Claude Sonnet 4.5 (reasoning)
- **Tools**: `parse_donation_offer`, `check_cold_chain_requirements`, `accept_donation`, `negotiate_pickup_time`, `generate_tax_receipt`

### Volunteer Agent
- **Role**: Matches volunteers to shifts and manages engagement
- **Model**: Claude Sonnet 4.5 (reasoning)
- **Tools**: `get_open_shifts`, `match_volunteer`, `send_shift_offer_sms`, `handle_no_show`, `calculate_volunteer_stats`

### Recipient Agent
- **Role**: Helps people find food and resources
- **Model**: Claude Sonnet 4.5 (reasoning)
- **Tools**: `find_nearest_pantry`, `check_pantry_hours`, `verify_eligibility`, `list_available_items`, `translate_response`

### Logistics Agent
- **Role**: Routes food from donors to distribution points
- **Model**: Claude Sonnet 4.5 (reasoning)
- **Tools**: `optimize_route`, `generate_manifest`, `dispatch_driver`, `track_cold_chain`

### Compliance Agent
- **Role**: Handles reporting, audits, and regulatory compliance
- **Model**: Claude Sonnet 4.5 (reasoning)
- **Tools**: `generate_usda_report`, `log_food_safety_event`, `generate_tax_receipt_batch`, `audit_trail`

## Adding a New Tool

```python
from strands import tool

@tool
def my_new_tool(param1: str, param2: int) -> dict:
    """Description of what this tool does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        dict with result data
    """
    # Implementation
    return {"result": "success"}
```

## Adding a New Agent

1. Create `haven/agents/my_agent.py`
2. Define the system prompt
3. Create the agent with `Agent(system_prompt=..., tools=[...])`
4. Register in `haven/agents/supervisor.py`

## Escalation Rules

Agents escalate to humans when:
- Donation value > $5,000
- Food safety incident detected
- Volunteer safety concern
- Recipient complaint
- Agent confidence < 70%
- Conflicting recommendations between agents
