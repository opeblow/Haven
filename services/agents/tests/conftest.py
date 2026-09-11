"""Pytest configuration and shared fixtures for Haven tests."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch):
    """Set required environment variables for tests."""
    monkeypatch.setenv("HAVEN_BEDROCK_MODEL_ID", "test-model")
    monkeypatch.setenv("HAVEN_DONATIONS_TABLE", "test-donations")
    monkeypatch.setenv("HAVEN_VOLUNTEERS_TABLE", "test-volunteers")
    monkeypatch.setenv("HAVEN_RECIPIENTS_TABLE", "test-recipients")
    monkeypatch.setenv("HAVEN_SHIFTS_TABLE", "test-shifts")
    monkeypatch.setenv("HAVEN_EVENTS_TABLE", "test-events")
    monkeypatch.setenv("HAVEN_AUDIT_TABLE", "test-audit")
    monkeypatch.setenv("HAVEN_API_HOST", "127.0.0.1")
    monkeypatch.setenv("HAVEN_API_PORT", "8001")
    monkeypatch.setenv("HAVEN_CORS_ORIGINS", '["http://localhost:3000"]')


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB resource and tables."""
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    mock_table.get_item.return_value = {"Item": {"id": "test-id", "name": "test"}}
    mock_table.scan.return_value = {"Items": []}
    mock_table.query.return_value = {"Items": []}
    mock_table.update_item.return_value = {}

    mock_dynamodb_resource = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table

    with patch("haven.db.get_dynamodb_resource", return_value=mock_dynamodb_resource):
        yield mock_dynamodb_resource, mock_table


@pytest.fixture
def mock_boto3_translate():
    """Mock boto3 Translate client."""
    mock_client = MagicMock()
    mock_client.translate_text.return_value = {
        "TranslatedText": "Hola, como estas?",
        "SourceLanguageCode": "en",
        "TargetLanguageCode": "es",
    }
    with patch("boto3.client", return_value=mock_client):
        yield mock_client
