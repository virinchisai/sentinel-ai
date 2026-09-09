import pytest
import httpx
from backend.config import settings
from backend.connectors.google import GoogleAPI
from backend.mcp_server.connectors.gmail_client import GmailClient
from backend.mcp_server.connectors.calendar_client import CalendarClient


def test_google_oauth_refresh_and_fixed_upstream(monkeypatch):
    calls = []

    def handle(request):
        calls.append(request)
        if request.url.host == "oauth2.googleapis.com":
            assert b"grant_type=refresh_token" in request.content
            return httpx.Response(200, json={"access_token": "test-access"})
        assert request.headers["authorization"] == "Bearer test-access"
        return httpx.Response(200, json={"messages": []})

    original = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kw: original(transport=httpx.MockTransport(handle), **kw),
    )
    api = GoogleAPI(
        '{"client_id":"test","client_secret":"test","refresh_token":"test"}'
    )
    assert api.request("gmail", "GET", "messages") == {"messages": []}
    assert calls[1].url.host == "gmail.googleapis.com"


def test_real_gmail_draft_and_calendar_paths(monkeypatch):
    monkeypatch.setattr(settings, "gmail_credentials_json", "{}")
    monkeypatch.setattr(settings, "google_calendar_credentials_json", "{}")
    calls = []

    def request(self, service, method, path, **kwargs):
        calls.append((service, method, path, kwargs))
        if path.startswith("threads/"):
            return {
                "messages": [
                    {
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "test@example.com"},
                                {"name": "Subject", "value": "Incident"},
                                {"name": "Message-ID", "value": "<test>"},
                            ]
                        }
                    }
                ]
            }
        return {"id": "created"}

    monkeypatch.setattr(GoogleAPI, "request", request)
    assert GmailClient().draft_reply("thread-1", "Review evidence")["id"] == "created"
    assert calls[-1][2] == "drafts"
    assert "raw" in calls[-1][3]["json"]["message"]
    CalendarClient().create_event(
        "Review",
        "2026-09-10T10:00:00+00:00",
        "2026-09-10T11:00:00+00:00",
        ["test@example.com"],
    )
    assert calls[-1][2] == "calendars/primary/events"
    assert calls[-1][3]["params"]["sendUpdates"] == "all"
    with pytest.raises(ValueError):
        CalendarClient().create_event(
            "Bad", "2026-09-10T11:00:00+00:00", "2026-09-10T10:00:00+00:00"
        )


def test_sso_disabled_by_default():
    from backend.auth.oidc import config

    assert config() == {"enabled": False}


def test_oidc_signature_nonce_and_stable_account(monkeypatch):
    import json, time, jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from backend.auth.oidc import exchange, Exchange
    from backend.auth.models import get_session_factory, User
    from fastapi import HTTPException

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    jwk["kid"] = "local-test"
    monkeypatch.setattr(
        settings, "oidc_issuer", "https://sso.example.invalid/realms/test"
    )
    monkeypatch.setattr(settings, "oidc_client_id", "sentinel")
    claims = {
        "iss": settings.oidc_issuer,
        "aud": "sentinel",
        "sub": "stable-subject",
        "nonce": "n" * 24,
        "exp": int(time.time()) + 60,
        "iat": int(time.time()),
    }
    token = jwt.encode(claims, key, algorithm="RS256", headers={"kid": "local-test"})

    def handle(request):
        return httpx.Response(
            200,
            json={"id_token": token}
            if request.url.path.endswith("/token")
            else {"keys": [jwk]},
        )

    original = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kw: original(transport=httpx.MockTransport(handle), **kw),
    )
    with get_session_factory()() as db:
        result = exchange(
            Exchange(code="code", code_verifier="v" * 48, nonce="n" * 24), db
        )
        assert result["access_token"]
        exchange(Exchange(code="code", code_verifier="v" * 48, nonce="n" * 24), db)
        assert db.query(User).count() == 1
        with pytest.raises(HTTPException):
            exchange(
                Exchange(code="code", code_verifier="v" * 48, nonce="wrong" * 5), db
            )
