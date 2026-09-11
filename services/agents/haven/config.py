"""Configuration for Haven agents using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = {"env_prefix": "HAVEN_", "env_file": ".env", "extra": "ignore"}

    # AWS
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-sonnet-4-5-20250514-v1:0"
    bedrock_routing_model_id: str = "amazon.nova-micro-v1:0"

    # DynamoDB
    donations_table: str = "haven-donations"
    volunteers_table: str = "haven-volunteers"
    recipients_table: str = "haven-recipients"
    shifts_table: str = "haven-shifts"
    events_table: str = "haven-events"
    audit_table: str = "haven-audit"
    dynamodb_endpoint_url: str = ""

    # S3
    documents_bucket: str = "haven-documents"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Escalation
    escalation_slack_webhook: str = ""
    escalation_sms_numbers: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()
