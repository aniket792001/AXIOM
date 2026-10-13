"""Dynamic API provider quota & availability manager for Axiom.

Prevents request pipeline stalls when cloud LLM providers (e.g. Gemini, OpenAI)
return 429 Resource Exhausted by instantly routing subsequent nodes to
grounded deterministic local fallback.
"""

import time

_quota_cooldowns: dict[str, float] = {}


def is_valid_gemini_key(key: str | None) -> bool:
    """Return True if key looks like an actual Google Gemini API key (AIzaSy...)."""
    if not key:
        return False
    key_str = key.strip()
    return key_str.startswith("AIza") and len(key_str) >= 30


def is_provider_available(provider: str = "gemini") -> bool:
    """Check if the provider is currently available or in rate-limit cooldown."""
    if provider == "gemini":
        from axiom.config.settings import get_settings
        key = get_settings().gemini_api_key
        if not is_valid_gemini_key(key):
            return False
    elif provider == "openai":
        from axiom.config.settings import get_settings
        key = get_settings().openai_api_key
        if not key or key.startswith("your_") or not key.startswith("sk-"):
            return False

    cooldown_until = _quota_cooldowns.get(provider, 0.0)
    return time.time() >= cooldown_until


def report_quota_exhausted(provider: str = "gemini", cooldown_seconds: float = 60.0) -> None:
    """Mark a provider as unavailable for a cooldown window (default 60s)."""
    _quota_cooldowns[provider] = time.time() + cooldown_seconds


def report_provider_error(provider: str = "gemini", cooldown_seconds: float = 10.0) -> None:
    """Report transient provider error with short cooldown (default 10s)."""
    _quota_cooldowns[provider] = time.time() + cooldown_seconds


def clear_quota_cooldown(provider: str = "gemini") -> None:
    """Clear cooldown to allow immediate retry."""
    _quota_cooldowns.pop(provider, None)

