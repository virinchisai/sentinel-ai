"""SQLAlchemy models for users, roles, and audit log."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
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
    token_version = Column(Integer, default=0, nullable=False)
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


class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class Membership(Base):
    __tablename__ = "memberships"
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)


class Document(Base):
    __tablename__ = "documents"
    id = Column(String(36), primary_key=True)
    workspace_id = Column(
        String(36), ForeignKey("workspaces.id"), index=True, nullable=False
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    sha256 = Column(String(64), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="ready", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(String(60), primary_key=True)
    document_id = Column(
        String(36), ForeignKey("documents.id"), index=True, nullable=False
    )
    workspace_id = Column(String(36), index=True, nullable=False)
    text = Column(Text, nullable=False)
    page = Column(Integer, default=1)
    embedding = Column(Text, nullable=True)


class Conversation(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(180), index=True, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(String(36), nullable=False)
    session_id = Column(String(180), nullable=False)
    tool = Column(String(100), nullable=False)
    arguments = Column(Text, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    result = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)


class UsedRefresh(Base):
    __tablename__ = "used_refresh_tokens"
    jti = Column(String(36), primary_key=True)
    expires_at = Column(DateTime, nullable=False)


class ConnectorCredential(Base):
    __tablename__ = "connector_credentials"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    provider = Column(String(30), primary_key=True)
    encrypted = Column(Text, nullable=False)


class DocumentJob(Base):
    __tablename__ = "document_jobs"
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(String(36), nullable=False)
    name = Column(String(200), nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String(20), default="queued", nullable=False)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Match PostgreSQL foreign-key enforcement in local SQLite deployments/tests.
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3


@event.listens_for(Engine, "connect")
def sqlite_foreign_keys(connection, record):
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys=ON")
