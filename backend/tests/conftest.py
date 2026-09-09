import pytest
from sqlalchemy import create_engine
from backend.auth import models
from backend.config import settings


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    engine = create_engine("sqlite:///" + str(tmp_path / "test.db"))
    monkeypatch.setattr(models, "_engine", engine)
    monkeypatch.setattr(models, "_SessionLocal", None)
    monkeypatch.setattr(settings, "embedding_model", "")
    models.init_db()
    yield
    engine.dispose()


@pytest.fixture
def user():
    with models.get_session_factory()() as db:
        u = models.User(
            username="tester",
            email="test@example.com",
            hashed_password="unused",
            role=models.Role.USER,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        db.expunge(u)
        return u


@pytest.fixture
def actor(user):
    from backend.agents.policy import Actor
    from backend.auth.workspaces import resolve_workspace

    return Actor(user.id, resolve_workspace(user.id))
