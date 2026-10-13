"""Authentication, API Key Management, and Tenant Scoping for Axiom Gateway."""

from datetime import datetime, timezone
import hashlib
import secrets
from typing import Any, Dict, List, Optional
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

API_KEY_HEADER = APIKeyHeader(name="X-Axiom-Key", auto_error=False)

# In-memory API Key Store (production attaches to PostgreSQL / Redis)
_API_KEYS_DB: Dict[str, Dict[str, Any]] = {}


class APIKeyInfo(BaseModel):
    """Metadata for an issued API key."""
    key_id: str
    name: str
    tenant_id: str
    role: str = "member"  # admin, member, auditor
    created_at: str
    last_used: Optional[str] = None
    masked_key: str


def hash_key(raw_key: str) -> str:
    """Compute cryptographic hash of raw API key for secure lookup."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key(tenant_id: str, name: str, role: str = "member") -> Dict[str, Any]:
    """Generate a high-entropy production API key prefixed with 'ax_live_'."""
    random_part = secrets.token_hex(20)
    raw_key = f"ax_live_{random_part}"
    key_id = f"key_{secrets.token_hex(6)}"
    hashed = hash_key(raw_key)
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "key_id": key_id,
        "name": name,
        "tenant_id": tenant_id,
        "role": role,
        "created_at": now,
        "last_used": None,
        "hashed_key": hashed,
        "masked_key": f"ax_live_{random_part[:4]}...{random_part[-4:]}",
    }
    _API_KEYS_DB[hashed] = record

    return {
        "raw_key": raw_key,
        "key_id": key_id,
        "name": name,
        "tenant_id": tenant_id,
        "role": role,
        "created_at": now,
    }


def list_api_keys(tenant_id: str) -> List[Dict[str, Any]]:
    """List all API keys belonging to a specific tenant."""
    results = []
    for record in _API_KEYS_DB.values():
        if record["tenant_id"] == tenant_id:
            results.append({
                "key_id": record["key_id"],
                "name": record["name"],
                "tenant_id": record["tenant_id"],
                "role": record["role"],
                "created_at": record["created_at"],
                "last_used": record["last_used"],
                "masked_key": record["masked_key"],
            })
    return sorted(results, key=lambda x: x["created_at"], reverse=True)


def revoke_api_key(tenant_id: str, key_id: str) -> bool:
    """Revoke an API key by key_id."""
    for hashed, record in list(_API_KEYS_DB.items()):
        if record["tenant_id"] == tenant_id and record["key_id"] == key_id:
            del _API_KEYS_DB[hashed]
            return True
    return False


async def get_current_tenant_and_role(
    x_axiom_key: Optional[str] = Security(API_KEY_HEADER),
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-ID"),
) -> Dict[str, str]:
    """Resolve current tenant and role from API key header or fallback to request header / default."""
    if x_axiom_key:
        hashed = hash_key(x_axiom_key)
        record = _API_KEYS_DB.get(hashed)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Axiom API Key.",
            )
        record["last_used"] = datetime.now(timezone.utc).isoformat()
        return {"tenant_id": record["tenant_id"], "role": record["role"]}

    tenant = x_tenant_id or "default_tenant"
    return {"tenant_id": tenant, "role": "admin"}
