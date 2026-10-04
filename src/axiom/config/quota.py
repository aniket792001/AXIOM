"""Dynamic API provider quota & availability manager for Axiom.

Prevents request pipeline stalls when cloud LLM providers (e.g. Gemini, OpenAI)
return 429 Resource Exhausted by instantly routing subsequent nodes to
grounded deterministic local fallback.
"""

import time

_quota_cooldowns: dict[str, float] = {}


def is_provider_available(provider: str = "gemini") -> bool:
    """Check if the provider is currently available or in rate-limit cooldown."""
    cooldown_until = _quota_cooldowns.get(provider, 0.0)
    return time.time() >= cooldown_until


def report_quota_exhausted(provider: str = "gemini", cooldown_seconds: float = 60.0) -> None:
    """Mark a provider as quota-exhausted for a cooldown window (default 60s)."""
    _quota_cooldowns[provider] = time.time() + cooldown_seconds


def clear_quota_cooldown(provider: str = "gemini") -> None:
    """Clear cooldown to allow immediate retry."""
    _quota_cooldowns.pop(provider, None)
