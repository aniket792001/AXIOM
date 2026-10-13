"""Unified Multi-Provider LLM Factory for Axiom & SCORE Engine.

Supports runtime switching between Google Gemini, OpenAI, Anthropic,
and local providers with Bring-Your-Own-Key (BYOK) enterprise support.
"""

from typing import Any, Optional
from axiom.config.quota import is_provider_available
from axiom.config.settings import get_settings


def get_chat_model(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.1,
    timeout: float = 25.0,
) -> Optional[Any]:
    """Instantiate a unified Chat model client based on requested provider or global settings.

    Returns None if no API key is available or the provider is in quota cooldown.
    """
    settings = get_settings()
    active_provider = (provider or "gemini").lower()

    # 1. Google Gemini
    if active_provider in ("gemini", "google"):
        key = api_key or settings.gemini_api_key
        if key and is_provider_available("gemini"):
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                model = model_name or settings.reasoning_model
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=key,
                    temperature=temperature,
                    max_retries=1,
                    request_timeout=timeout,
                )
            except Exception:
                pass

    # 2. OpenAI
    if active_provider == "openai" or (not provider and settings.openai_api_key):
        key = api_key or settings.openai_api_key
        if key and is_provider_available("openai"):
            try:
                from langchain_openai import ChatOpenAI
                model = model_name or (
                    settings.reasoning_model if "gpt" in settings.reasoning_model else "gpt-4o-mini"
                )
                return ChatOpenAI(
                    model=model,
                    api_key=key,
                    temperature=temperature,
                    request_timeout=timeout,
                )
            except Exception:
                pass

    # 3. Anthropic
    if active_provider == "anthropic" or (not provider and settings.anthropic_api_key):
        key = api_key or settings.anthropic_api_key
        if key and is_provider_available("anthropic"):
            try:
                from langchain_anthropic import ChatAnthropic
                model = model_name or "claude-3-5-sonnet-20240620"
                return ChatAnthropic(
                    model_name=model,
                    anthropic_api_key=key,
                    temperature=temperature,
                    timeout=timeout,
                )
            except Exception:
                pass

    return None
