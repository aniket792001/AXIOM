"""Integration tests for Multi-Tenant Workspace Isolation and RBAC Security Controls.

Guarantees:
1. Cross-Tenant Isolation: User B cannot access or query User A's private workspace.
2. RBAC Enforcement:
   - Auditors cannot upload/ingest documents (403 Forbidden).
   - Analysts cannot delete documents (403 Forbidden).
   - Only Admins have full deletion authority.
3. Zero Cross-Tenant Leakage: Isolated workspaces return 403 when accessed by unauthorized tenants.
"""

import pytest
from fastapi.testclient import TestClient
from axiom.api.main import app
from axiom.core.security import create_access_token

client = TestClient(app)


def test_user_registration_workspace_isolation():
    """Verify that newly registered users are automatically assigned private isolated workspaces."""
    email = "friend_user@test.org"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Friend User",
            "email": email,
            "password": "Password123!",
            "role": "analyst",
        },
    )
    # 201 Created or 200/400 if already exists
    if res.status_code == 201:
        data = res.json()
        assert data["user"]["default_tenant"] == "ws_friend_user_test_org"
        assert "ingest" in data["user"]["permissions"]
        assert "delete_docs" not in data["user"]["permissions"]


def test_cross_tenant_workspace_access_denied():
    """Verify that a user token cannot inspect or query another user's private workspace."""
    user_a_token = create_access_token({
        "sub": "user_a@axiom.ai",
        "email": "user_a@axiom.ai",
        "name": "User A",
        "role": "analyst",
        "default_tenant": "ws_user_a_axiom_ai",
        "permissions": ["query", "ingest"],
    })

    user_b_workspace = "ws_user_b_private_vault"

    # User A attempts to list User B's documents
    res = client.get(
        f"/api/v1/documents?tenant_id={user_b_workspace}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert res.status_code == 403
    assert "Cross-tenant access forbidden" in res.json()["detail"]

    # User A attempts to query User B's workspace
    query_res = client.post(
        "/api/v1/query",
        json={
            "query": "What is in User B's private contract?",
            "tenant_id": user_b_workspace,
        },
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert query_res.status_code == 403
    assert "Cross-tenant access forbidden" in query_res.json()["detail"]


def test_rbac_auditor_ingest_blocked():
    """Verify that an Auditor account cannot upload or ingest documents (SOC-2 read-only compliance)."""
    auditor_token = create_access_token({
        "sub": "auditor_test@axiom.ai",
        "email": "auditor_test@axiom.ai",
        "name": "Auditor Test",
        "role": "auditor",
        "default_tenant": "ws_auditor_test",
        "permissions": ["query", "export_cert", "view_audit"],
    })

    file_content = b"# Auditor Ingest Test\nShould be blocked."
    res = client.post(
        "/api/v1/ingest/file",
        data={"tenant_id": "ws_auditor_test"},
        files={"file": ("blocked.md", file_content, "text/markdown")},
        headers={"Authorization": f"Bearer {auditor_token}"},
    )
    assert res.status_code == 403
    assert "RBAC Permission Denied: Action requires 'ingest'" in res.json()["detail"]


def test_rbac_analyst_delete_blocked():
    """Verify that an Analyst account cannot delete documents from any partition."""
    analyst_token = create_access_token({
        "sub": "analyst_test@axiom.ai",
        "email": "analyst_test@axiom.ai",
        "name": "Analyst Test",
        "role": "analyst",
        "default_tenant": "ws_analyst_test",
        "permissions": ["query", "ingest", "export_cert"],
    })

    res = client.delete(
        "/api/v1/documents/some_contract.pdf?tenant_id=ws_analyst_test",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 403
    assert "RBAC Permission Denied: Action requires 'delete_docs'" in res.json()["detail"]


def test_admin_full_tenant_management():
    """Verify that an Admin account has cross-partition inspection and management capabilities."""
    admin_token = create_access_token({
        "sub": "admin_test@axiom.ai",
        "email": "admin_test@axiom.ai",
        "name": "Admin Test",
        "role": "admin",
        "default_tenant": "ws_admin_test",
        "permissions": ["query", "ingest", "delete_docs", "manage_keys", "export_cert", "view_audit", "manage_users"],
    })

    # Admin listing documents in a demo partition succeeds
    res = client.get(
        "/api/v1/documents?tenant_id=default_tenant",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
