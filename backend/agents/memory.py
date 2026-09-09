"""Persist complete provider messages, preserving tool call identities."""

import json
from backend.auth.models import Conversation, get_session_factory


def get_history(session_id):
    with get_session_factory()() as db:
        rows = (
            db.query(Conversation)
            .filter_by(session_id=session_id)
            .order_by(Conversation.id)
            .all()
        )
        return [json.loads(row.message) for row in rows]


def append(session_id, message):
    def encode(value):
        if hasattr(value, "model_dump"):
            return value.model_dump()
        raise TypeError(type(value).__name__)

    with get_session_factory()() as db:
        db.add(
            Conversation(
                session_id=session_id, message=json.dumps(message, default=encode)
            )
        )
        db.commit()


def reset(session_id):
    with get_session_factory()() as db:
        db.query(Conversation).filter_by(session_id=session_id).delete()
        db.commit()


def list_sessions(prefix=""):
    from sqlalchemy import func

    with get_session_factory()() as db:
        rows = (
            db.query(
                Conversation.session_id, func.count(), func.max(Conversation.created_at)
            )
            .filter(Conversation.session_id.startswith(prefix))
            .group_by(Conversation.session_id)
            .all()
        )
        return [
            {"session_id": r[0], "message_count": r[1], "last_active": r[2].isoformat()}
            for r in rows
        ]
