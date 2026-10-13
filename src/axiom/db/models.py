"""SQLAlchemy ORM models for Axiom Customer History & Auth."""

from datetime import datetime
from typing import Any, Dict
import json
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """User account model for enterprise personas & customer logins."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="analyst")  # admin, analyst, auditor
    title = Column(String(255), default="Enterprise User")
    default_tenant = Column(String(100), default="default_tenant")
    avatar = Column(String(10), default="U")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        from axiom.core.security import hash_password
        self.hashed_password = hash_password(password)

    def verify_password(self, password: str) -> bool:
        """Check provided password against stored Bcrypt hash."""
        from axiom.core.security import verify_password
        if not self.hashed_password:
            return False
        return verify_password(password, self.hashed_password)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to safe dict representation (never leaks hashed_password)."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "title": self.title,
            "default_tenant": self.default_tenant,
            "avatar": self.avatar,
            "is_active": self.is_active if self.is_active is not None else True,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class SessionThread(Base):
    """Conversation session thread for a customer workspace."""
    __tablename__ = "session_threads"

    id = Column(String(100), primary_key=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class QueryRecord(Base):
    """Full historical record of a reasoning query and retrieval audit."""
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    rewritten_query = Column(Text, nullable=True)
    route = Column(String(50), default="vector_store")
    generation = Column(Text, nullable=False, default="")
    citations_json = Column(Text, default="[]")
    retrieved_chunks_json = Column(Text, default="[]")
    hallucination_status = Column(String(50), default="grounded")
    loop_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        citations = []
        try:
            citations = json.loads(self.citations_json) if self.citations_json else []
        except Exception:
            citations = []

        return {
            "id": self.id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "query": self.query,
            "rewritten_query": self.rewritten_query,
            "route": self.route,
            "generation": self.generation,
            "citations": citations,
            "hallucination_status": self.hallucination_status,
            "loop_count": self.loop_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DocumentMetadata(Base):
    """Catalog of uploaded files across partitioned tenant data rooms."""
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    filename = Column(String(255), nullable=False, index=True)
    chunk_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    uploaded_by = Column(String(255), default="anonymous")
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "filename": self.filename,
            "chunk_count": self.chunk_count,
            "char_count": self.char_count,
            "page_count": self.page_count,
            "uploaded_by": self.uploaded_by,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
