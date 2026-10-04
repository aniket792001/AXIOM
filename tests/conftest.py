"""Pytest root fixtures and test configuration for Axiom & SCORE Engine."""

import os
import pytest
from axiom.config.settings import get_settings


@pytest.fixture(autouse=True)
def isolated_test_environment(monkeypatch):
    """Ensure unit and integration tests run deterministically in local test mode."""
    # Unset live cloud keys during automated test runs to prevent quota throttling
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("COHERE_API_KEY", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
