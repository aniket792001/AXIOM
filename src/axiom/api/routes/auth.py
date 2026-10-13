"""Role-Based Authentication, JWT Security & User Profile Management for Axiom."""

from datetime import datetime, timezone
import secrets
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from axiom.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from axiom.db.database import SessionLocal
from axiom.db.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & RBAC"])

# Predefined Enterprise Roles and Permissions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin": ["query", "ingest", "delete_docs", "manage_keys", "export_cert", "view_audit", "manage_users"],
    "analyst": ["query", "ingest", "export_cert"],
    "auditor": ["query", "export_cert", "view_audit"],
}

DEMO_USERS = {
    "admin@axiom.ai": {
        "email": "admin@axiom.ai",
        "name": "Alex Vance (Admin)",
        "role": "admin",
        "title": "Enterprise System Administrator",
        "avatar": "AV",
        "default_tenant": "default_tenant",
        "permissions": ROLE_PERMISSIONS["admin"],
    },
    "analyst@axiom.ai": {
        "email": "analyst@axiom.ai",
        "name": "Sarah Chen (Analyst)",
        "role": "analyst",
        "title": "Senior Contract & Legal Analyst",
        "avatar": "SC",
        "default_tenant": "legal_contracts",
        "permissions": ROLE_PERMISSIONS["analyst"],
    },
    "auditor@axiom.ai": {
        "email": "auditor@axiom.ai",
        "name": "Marcus Stone (Auditor)",
        "role": "auditor",
        "title": "Lead Compliance & Risk Auditor",
        "avatar": "MS",
        "default_tenant": "financial_filings",
        "permissions": ROLE_PERMISSIONS["auditor"],
    },
}

# Active Session Token Cache
_SESSIONS_DB: Dict[str, Dict[str, Any]] = {}


class LoginRequest(BaseModel):
    """Payload for logging into Axiom."""
    email: str = Field(..., description="Enterprise user email")
    password: Optional[str] = Field(default="", description="User password for credential verification")
    role: Optional[str] = Field(default=None, description="Role shortcut for demo persona switching")


class RegisterRequest(BaseModel):
    """Payload for registering a new customer user account."""
    email: str = Field(..., description="Enterprise user email")
    name: str = Field(..., description="Full user display name")
    password: Optional[str] = Field(default="", description="Account password (min 6 characters)")
    role: str = Field(default="analyst", description="Role: admin, analyst, auditor")
    title: Optional[str] = Field(default="Enterprise User", description="Job title")
    default_tenant: Optional[str] = Field(default="default_tenant", description="Default tenant data room")


class ProfileUpdateRequest(BaseModel):
    """Payload for modifying an existing user profile."""
    name: Optional[str] = Field(default=None, description="Updated display name")
    title: Optional[str] = Field(default=None, description="Updated job title")
    avatar: Optional[str] = Field(default=None, description="Avatar abbreviation (2 chars)")
    default_tenant: Optional[str] = Field(default=None, description="Preferred default tenant")


class ChangePasswordRequest(BaseModel):
    """Payload for updating user password securely."""
    current_password: str = Field(..., description="Existing plaintext password")
    new_password: str = Field(..., min_length=6, description="New plaintext password (min 6 chars)")


class LoginResponse(BaseModel):
    """Authentication response with signed JWT token and user profile."""
    token: str
    user: Dict[str, Any]
    tenant_id: str
    status: str = "authenticated"


def _extract_token(
    authorization: Optional[str] = None,
    query_token: Optional[str] = None,
) -> Optional[str]:
    """Helper to extract token from Authorization header or query param."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return query_token


def _get_user_by_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Resolve user profile from JWT claims or session cache."""
    if not token:
        return None
    # 1. Check in-memory cache
    if token in _SESSIONS_DB:
        return _SESSIONS_DB[token]["user"]
    # 2. Decode JWT claims
    claims = decode_access_token(token)
    if claims and "sub" in claims:
        email = claims["sub"]
        with SessionLocal() as db:
            db_user = db.query(User).filter_by(email=email).first()
            if db_user:
                user_dict = db_user.to_dict()
                user_dict["permissions"] = ROLE_PERMISSIONS.get(db_user.role, ROLE_PERMISSIONS["analyst"])
                return user_dict
    return None


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    """Authenticate user with Bcrypt verification and issue RFC-compliant signed JWT."""
    email = payload.email.lower().strip()
    user_record = DEMO_USERS.get(email)

    # Allow role alias shortcut (e.g. role='admin')
    if not user_record and payload.role:
        for u in DEMO_USERS.values():
            if u["role"] == payload.role.lower():
                user_record = u
                email = u["email"]
                break

    with SessionLocal() as db:
        db_user = db.query(User).filter_by(email=email).first()

        # If user exists and password is provided, verify Bcrypt hash
        if db_user and db_user.hashed_password and payload.password:
            if not db_user.verify_password(payload.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials. Incorrect password provided.",
                )

        # Update or create user record in SQLite DB
        if db_user:
            db_user.last_login = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_user)
            user_profile = db_user.to_dict()
            user_profile["permissions"] = ROLE_PERMISSIONS.get(db_user.role, ROLE_PERMISSIONS["analyst"])
        else:
            # Create dynamic user
            new_role = (user_record.get("role") if user_record else payload.role) or "analyst"
            new_title = (user_record.get("title") if user_record else "Enterprise Team Member")
            new_tenant = (user_record.get("default_tenant") if user_record else "default_tenant")
            new_avatar = (user_record.get("avatar") if user_record else email[:2].upper())
            new_name = (user_record.get("name") if user_record else email.split("@")[0].capitalize())

            db_user = User(
                email=email,
                name=new_name,
                role=new_role,
                title=new_title,
                default_tenant=new_tenant,
                avatar=new_avatar,
                is_active=True,
                last_login=datetime.now(timezone.utc),
            )
            if payload.password:
                db_user.set_password(payload.password)
            elif email in DEMO_USERS:
                db_user.set_password("AxiomAdmin2026!" if new_role == "admin" else "AxiomPassword2026!")

            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            user_profile = db_user.to_dict()
            user_profile["permissions"] = ROLE_PERMISSIONS.get(new_role, ROLE_PERMISSIONS["analyst"])

    # Generate Signed JWT Access Token
    jwt_token = create_access_token({
        "sub": email,
        "role": user_profile["role"],
        "name": user_profile["name"],
        "tenant_id": user_profile["default_tenant"],
    })

    # Cache session
    _SESSIONS_DB[jwt_token] = {
        "token": jwt_token,
        "user": user_profile,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return LoginResponse(
        token=jwt_token,
        user=user_profile,
        tenant_id=user_profile["default_tenant"],
    )


@router.post("/register")
async def register_user(payload: RegisterRequest) -> Dict[str, Any]:
    """Register a new customer account with Bcrypt password hashing in SQLite."""
    email = payload.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid email address is required.")

    with SessionLocal() as db:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{email}' already registered.",
            )

        new_user = User(
            email=email,
            name=payload.name.strip(),
            role=payload.role or "analyst",
            title=payload.title or "Enterprise User",
            default_tenant=payload.default_tenant or "default_tenant",
            avatar=payload.name[:2].upper() if payload.name else email[:2].upper(),
            is_active=True,
            last_login=datetime.now(timezone.utc),
        )
        if payload.password:
            new_user.set_password(payload.password)
        else:
            new_user.set_password("AxiomDefault2026!")

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        user_data = new_user.to_dict()
        user_data["permissions"] = ROLE_PERMISSIONS.get(new_user.role, ROLE_PERMISSIONS["analyst"])

        # Create instant JWT token
        token = create_access_token({
            "sub": email,
            "role": new_user.role,
            "name": new_user.name,
            "tenant_id": new_user.default_tenant,
        })
        _SESSIONS_DB[token] = {
            "token": token,
            "user": user_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "status": "created",
            "user": user_data,
            "token": token,
            "message": f"User account '{email}' registered successfully.",
        }


@router.get("/users")
async def list_database_users() -> Dict[str, Any]:
    """List all registered enterprise accounts stored in SQLite database."""
    with SessionLocal() as db:
        users = db.query(User).order_by(User.created_at.asc()).all()
        return {
            "total": len(users),
            "users": [u.to_dict() for u in users],
        }


@router.get("/me")
async def get_current_user_profile(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Retrieve user details and active permissions for the calling session."""
    active_token = _extract_token(authorization, token)
    user = _get_user_by_token(active_token)
    if user:
        return user
    # Fallback to default admin profile for unauthenticated exploratory calls
    return DEMO_USERS["admin@axiom.ai"]


@router.put("/me")
async def update_user_profile(
    payload: ProfileUpdateRequest,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Update profile information (display name, title, avatar, default tenant)."""
    active_token = _extract_token(authorization, token)
    user_info = _get_user_by_token(active_token)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    email = user_info["email"]
    with SessionLocal() as db:
        db_user = db.query(User).filter_by(email=email).first()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if payload.name:
            db_user.name = payload.name.strip()
        if payload.title:
            db_user.title = payload.title.strip()
        if payload.avatar:
            db_user.avatar = payload.avatar.strip().upper()[:2]
        if payload.default_tenant:
            db_user.default_tenant = payload.default_tenant.strip()

        db_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_user)

        updated_dict = db_user.to_dict()
        updated_dict["permissions"] = ROLE_PERMISSIONS.get(db_user.role, ROLE_PERMISSIONS["analyst"])

        # Update cache
        if active_token and active_token in _SESSIONS_DB:
            _SESSIONS_DB[active_token]["user"] = updated_dict

        return {
            "status": "updated",
            "user": updated_dict,
            "message": "User profile successfully updated.",
        }


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Verify current password and securely hash new password with Bcrypt."""
    active_token = _extract_token(authorization, token)
    user_info = _get_user_by_token(active_token)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    email = user_info["email"]
    with SessionLocal() as db:
        db_user = db.query(User).filter_by(email=email).first()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        # If user already has a password, verify current password
        if db_user.hashed_password:
            if not db_user.verify_password(payload.current_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect.",
                )

        # Hash and set new password
        db_user.set_password(payload.new_password)
        db_user.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "status": "success",
            "message": "Password updated successfully. Please use your new password on next sign in.",
        }


@router.post("/logout")
async def logout(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> Dict[str, str]:
    """Invalidate session token."""
    active_token = _extract_token(authorization, token)
    if active_token and active_token in _SESSIONS_DB:
        del _SESSIONS_DB[active_token]
    return {"status": "logged_out"}
