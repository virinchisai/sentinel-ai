"""SQLAlchemy models for users, roles, and audit log."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from backend.config import settings


class Base(DeclarativeBase):
    pass


class Role(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(Role), default=Role.USER, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    audit_entries = relationship("AuditLog", back_populates="user")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(255), nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_entries")


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, echo=False)
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def get_db() -> Session:
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
