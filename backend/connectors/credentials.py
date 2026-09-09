"""Encrypted per-user credentials; never include secret values in API responses."""

import base64
import hashlib
import json
import os
from cryptography.fernet import Fernet
from backend.auth.models import ConnectorCredential, get_session_factory
from backend.config import settings


def cipher():
    return Fernet(
        base64.urlsafe_b64encode(
            hashlib.sha256(settings.jwt_secret_key.encode()).digest()
        )
    )


def save(user_id, provider, value):
    with get_session_factory()() as db:
        row = db.get(ConnectorCredential, (user_id, provider))
        if not row:
            row = ConnectorCredential(user_id=user_id, provider=provider)
            db.add(row)
        row.encrypted = cipher().encrypt(json.dumps(value).encode()).decode()
        db.commit()


def read(user_id, provider):
    with get_session_factory()() as db:
        row = db.get(ConnectorCredential, (user_id, provider))
        return json.loads(cipher().decrypt(row.encrypted.encode())) if row else None


def connector_environment(user_id):
    # Explicit empty values prevent fallback to host-wide connector credentials.
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        in {
            "PATH",
            "HOME",
            "SYSTEMROOT",
            "VIRTUAL_ENV",
            "PYTHONPATH",
            "DATABASE_URL",
            "DATA_DIR",
            "JWT_SECRET_KEY",
            "WORKSPACE_DIR",
            "OLLAMA_BASE_URL",
        }
    }
    github = read(user_id, "github")
    google = read(user_id, "google")
    env.update(
        DATABASE_URL=settings.database_url,
        TOOL_DATABASE_URL=settings.tool_database_url,
        WORKSPACE_DIR=settings.workspace_dir,
    )
    env.update(
        GITHUB_TOKEN=github["token"] if github else "",
        GMAIL_CREDENTIALS_JSON=json.dumps(google) if google else "",
        GOOGLE_CALENDAR_CREDENTIALS_JSON=json.dumps(google) if google else "",
    )
    return env
