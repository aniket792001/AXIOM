"""API Key Management Routes for Axiom Platform."""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from axiom.api.auth import generate_api_key, list_api_keys, revoke_api_key

router = APIRouter(prefix="/api/v1/keys", tags=["Developer Platform & API Keys"])


class CreateKeyRequest(BaseModel):
    """Payload to create an API key."""
    name: str = Field(..., description="Descriptive name (e.g. 'Production Legal Bot')")
    tenant_id: str = Field(default="default_tenant", description="Associated tenant workspace")
    role: str = Field(default="member", description="Access role: admin, member, auditor")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_key(payload: CreateKeyRequest) -> Dict[str, Any]:
    """Issue a new scoped API Key for external application integration."""
    return generate_api_key(
        tenant_id=payload.tenant_id,
        name=payload.name,
        role=payload.role,
    )


@router.get("", response_model=List[Dict[str, Any]])
async def get_keys(
    tenant_id: str = Query(default="default_tenant", description="Associated tenant workspace"),
) -> List[Dict[str, Any]]:
    """List all issued API keys for a tenant with masked tokens."""
    return list_api_keys(tenant_id=tenant_id)


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
async def delete_key(
    key_id: str,
    tenant_id: str = Query(default="default_tenant", description="Associated tenant workspace"),
) -> Dict[str, Any]:
    """Revoke and invalidate an API key."""
    success = revoke_api_key(tenant_id=tenant_id, key_id=key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key '{key_id}' not found for tenant '{tenant_id}'.",
        )
    return {"status": "success", "key_id": key_id, "message": "API key revoked successfully."}
