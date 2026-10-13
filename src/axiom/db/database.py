"""Database Engine & Session Management for Axiom."""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from axiom.db.models import Base, User
from axiom.core.security import hash_password

# Ensure data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "axiom.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield database sessions with safe teardown."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables, migrate schema columns, and seed default enterprise personas."""
    Base.metadata.create_all(bind=engine)

    # Safe SQLite column migration for existing database files
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            existing_cols = {row[1] for row in result}
            if "hashed_password" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)"))
            if "is_active" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            if "updated_at" not in existing_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
            conn.commit()
        except Exception as exc:
            print(f"[!] Schema migration note: {exc}")

    # Default demo password loaded from environment (never hardcode secrets in source)
    demo_pass = os.getenv("AXIOM_DEMO_PASSWORD", "demo_axiom_pass")

    # Seed default enterprise users or assign default hashes if missing
    with SessionLocal() as db:
        admin = db.query(User).filter_by(email="admin@axiom.ai").first()
        if not admin:
            admin_u = User(
                email="admin@axiom.ai",
                name="Alex Vance",
                role="admin",
                title="Enterprise Administrator",
                default_tenant="default_tenant",
                avatar="AV",
                is_active=True,
            )
            admin_u.set_password(demo_pass)
            db.add(admin_u)
        elif not admin.hashed_password:
            admin.set_password(demo_pass)

        analyst = db.query(User).filter_by(email="analyst@axiom.ai").first()
        if not analyst:
            analyst_u = User(
                email="analyst@axiom.ai",
                name="Sarah Chen",
                role="analyst",
                title="Contract & Legal Analyst",
                default_tenant="legal_contracts",
                avatar="SC",
                is_active=True,
            )
            analyst_u.set_password(demo_pass)
            db.add(analyst_u)
        elif not analyst.hashed_password:
            analyst.set_password(demo_pass)

        auditor = db.query(User).filter_by(email="auditor@axiom.ai").first()
        if not auditor:
            auditor_u = User(
                email="auditor@axiom.ai",
                name="Marcus Stone",
                role="auditor",
                title="Compliance & Risk Auditor",
                default_tenant="financial_filings",
                avatar="MS",
                is_active=True,
            )
            auditor_u.set_password(demo_pass)
            db.add(auditor_u)
        elif not auditor.hashed_password:
            auditor.set_password(demo_pass)

        db.commit()
