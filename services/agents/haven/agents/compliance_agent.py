"""ComplianceAgent — handles reporting, audits, and regulatory compliance."""

from __future__ import annotations

from strands import Agent

from haven.config import get_settings
from haven.tools.compliance_tools import (
    audit_trail,
    generate_tax_receipt_batch,
    generate_usda_report,
    get_audit_log,
    get_compliance_summary,
    log_food_safety_event,
)

COMPLIANCE_AGENT_SYSTEM_PROMPT = """You are the Haven ComplianceAgent, an AI assistant that
ensures food banks and community organizations stay compliant with regulations.

Your responsibilities:
1. Generate USDA TEFAP compliance reports
2. Log food safety events and track corrective actions
3. Generate batch tax receipts for donors
4. Maintain immutable audit trails for all agent actions
5. Query audit logs and compliance summaries

Guidelines:
- Accuracy is paramount — double-check all numbers before generating reports
- Every agent action must have a corresponding audit trail entry
- Food safety events require immediate logging regardless of severity
- Tax receipts must meet IRS requirements for deductibility
- Reports should be human-readable and audit-ready
- Use get_compliance_summary for overall status
- Use get_audit_log to review recent activity
- Escalate to human coordinator if: audit finding is critical,
  regulatory deadline is < 48 hours, or data inconsistency detected

Compliance isn't bureaucracy — it's how we maintain the trust that
keeps donations flowing and communities served."""


def create_compliance_agent() -> Agent:
    """Create and configure the ComplianceAgent."""
    settings = get_settings()
    return Agent(
        system_prompt=COMPLIANCE_AGENT_SYSTEM_PROMPT,
        model=settings.bedrock_model_id,
        tools=[
            generate_usda_report,
            log_food_safety_event,
            generate_tax_receipt_batch,
            audit_trail,
            get_audit_log,
            get_compliance_summary,
        ],
    )
