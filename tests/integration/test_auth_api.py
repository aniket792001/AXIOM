"""Integration tests for Role-Based Authentication & Session API."""

import pytest
from fastapi.testclient import TestClient
from axiom.api.main import app

client = TestClient(app)


def test_auth_login_roles():
    """Verify login with preset enterprise roles (Admin, Analyst, Auditor)."""
    # 1. Admin login
    res_admin = client.post("/api/v1/auth/login", json={"email": "admin@axiom.ai", "role": "admin"})
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert data_admin["user"]["role"] == "admin"
    assert len(data_admin["token"]) > 20
    assert "delete_docs" in data_admin["user"]["permissions"]

    # 2. Analyst login
    res_analyst = client.post("/api/v1/auth/login", json={"email": "analyst@axiom.ai", "role": "analyst"})
    assert res_analyst.status_code == 200
    data_analyst = res_analyst.json()
    assert data_analyst["user"]["role"] == "analyst"
    assert data_analyst["tenant_id"] == "legal_contracts"

    # 3. Auditor login
    res_auditor = client.post("/api/v1/auth/login", json={"email": "auditor@axiom.ai", "role": "auditor"})
    assert res_auditor.status_code == 200
    data_auditor = res_auditor.json()
    assert data_auditor["user"]["role"] == "auditor"
    assert "view_audit" in data_auditor["user"]["permissions"]
    assert "delete_docs" not in data_auditor["user"]["permissions"]


def test_auth_password_verification_and_rejection():
    """Verify password-based authentication with Bcrypt and rejection of wrong password."""
    # Correct password for admin
    res_valid = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@axiom.ai", "password": "AxiomAdmin2026!"},
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["user"]["email"] == "admin@axiom.ai"

    # Incorrect password for admin
    res_invalid = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@axiom.ai", "password": "WrongPassword123!"},
    )
    assert res_invalid.status_code == 401
    assert "Incorrect password" in res_invalid.json()["detail"]


def test_auth_me_and_logout():
    """Verify session token validation and logout."""
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@axiom.ai"})
    token = login_res.json()["token"]

    # Check /me with token in query param
    me_res = client.get(f"/api/v1/auth/me?token={token}")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@axiom.ai"

    # Check /me with Authorization header Bearer token
    me_header_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_header_res.status_code == 200
    assert me_header_res.json()["email"] == "admin@axiom.ai"

    # Logout
    logout_res = client.post(f"/api/v1/auth/logout?token={token}")
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "logged_out"


def test_database_users_and_registration():
    """Verify customer registration, profile update, and password change."""
    # List users in SQLite DB
    res_list = client.get("/api/v1/auth/users")
    assert res_list.status_code == 200
    users_data = res_list.json()
    assert users_data["total"] >= 1
    assert any(u["email"] == "admin@axiom.ai" for u in users_data["users"])

    # Register a new customer with a password
    import time
    test_email = f"customer_{int(time.time())}@enterprise.com"
    initial_password = "SecurePassword123!"
    res_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_email,
            "name": "Jordan Smith",
            "password": initial_password,
            "role": "analyst",
            "title": "Risk Analyst",
            "default_tenant": "legal_contracts",
        },
    )
    assert res_reg.status_code == 200
    reg_data = res_reg.json()
    assert reg_data["status"] == "created"
    assert reg_data["user"]["email"] == test_email
    token = reg_data["token"]

    # Verify updating user profile (PUT /api/v1/auth/me)
    res_update = client.put(
        f"/api/v1/auth/me?token={token}",
        json={
            "name": "Jordan Smith, CFA",
            "title": "Lead Risk Analyst",
            "avatar": "JS",
            "default_tenant": "financial_filings",
        },
    )
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["user"]["name"] == "Jordan Smith, CFA"
    assert updated_data["user"]["title"] == "Lead Risk Analyst"
    assert updated_data["user"]["default_tenant"] == "financial_filings"

    # Verify changing password (POST /api/v1/auth/change-password)
    new_password = "UpdatedPassword2026!"
    # Wrong current password fails
    res_fail_change = client.post(
        f"/api/v1/auth/change-password?token={token}",
        json={"current_password": "WrongCurrentPassword!", "new_password": new_password},
    )
    assert res_fail_change.status_code == 400

    # Correct current password succeeds
    res_pwd_change = client.post(
        f"/api/v1/auth/change-password?token={token}",
        json={"current_password": initial_password, "new_password": new_password},
    )
    assert res_pwd_change.status_code == 200
    assert res_pwd_change.json()["status"] == "success"

    # Verify login with new password
    res_new_login = client.post(
        "/api/v1/auth/login",
        json={"email": test_email, "password": new_password},
    )
    assert res_new_login.status_code == 200
    assert res_new_login.json()["user"]["name"] == "Jordan Smith, CFA"


def test_history_audit_and_sessions_endpoints():
    """Verify audit log retrieval and session thread listing/deletion."""
    # List audit history from SQLite
    res_audit = client.get("/api/v1/history/audit")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert "records" in audit_data

    # List threads
    res_sessions = client.get("/api/v1/sessions")
    assert res_sessions.status_code == 200
    assert isinstance(res_sessions.json(), list)
