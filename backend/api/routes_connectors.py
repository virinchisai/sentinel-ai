"""Personal connector setup and active health checks."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, SecretStr
import httpx
from backend.auth.middleware import require_permission
from backend.auth.models import ConnectorCredential, get_session_factory
from backend.connectors.credentials import save, read
from backend.auth.audit import log_action
from backend.config import settings

router = APIRouter(prefix="/connectors", tags=["connectors"])


class Credentials(BaseModel):
    token: SecretStr | None = None
    client_id: str | None = None
    client_secret: SecretStr | None = None
    refresh_token: SecretStr | None = None


@router.put("/{provider}")
def configure(
    provider: str, body: Credentials, user=Depends(require_permission("use_tools"))
):
    if provider not in {"github", "google"}:
        raise HTTPException(400, "Unknown connector")
    value = {
        k: (v.get_secret_value() if isinstance(v, SecretStr) else v)
        for k, v in body
        if v is not None
    }
    required = (
        {"token"}
        if provider == "github"
        else {"client_id", "client_secret", "refresh_token"}
    )
    if not required.issubset(value):
        raise HTTPException(422, "Required credential fields are missing")
    save(user.id, provider, value)
    log_action(user.id, "connector.configure", provider)
    return {"status": "configured"}


@router.delete("/{provider}")
def disconnect(provider: str, user=Depends(require_permission("use_tools"))):
    with get_session_factory()() as db:
        db.query(ConnectorCredential).filter_by(
            user_id=user.id, provider=provider
        ).delete()
        db.commit()
    log_action(user.id, "connector.disconnect", provider)
    return {"status": "disconnected"}


@router.get("/status")
async def status(user=Depends(require_permission("chat"))):
    result = []
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(settings.ollama_base_url + "/api/tags")
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            result.append(
                {
                    "name": "Local model",
                    "mode": "live"
                    if settings.ollama_model in models
                    else "missing_model",
                    "detail": settings.ollama_model,
                }
            )
        except Exception:
            result.append(
                {
                    "name": "Local model",
                    "mode": "offline",
                    "detail": "Ollama is unavailable",
                }
            )
        token = read(user.id, "github")
        if token:
            try:
                r = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": "Bearer " + token["token"]},
                )
                result.append(
                    {
                        "name": "GitHub",
                        "mode": "live" if r.is_success else "error",
                        "detail": "Account check passed"
                        if r.is_success
                        else "Credentials rejected",
                    }
                )
            except Exception:
                result.append(
                    {"name": "GitHub", "mode": "offline", "detail": "Connection failed"}
                )
        else:
            result.append(
                {
                    "name": "GitHub",
                    "mode": "disconnected",
                    "detail": "Add a scoped personal token",
                }
            )
        result.append(
            {
                "name": "Google",
                "mode": "configured" if read(user.id, "google") else "disconnected",
                "detail": "OAuth credentials saved; permissions checked on use",
            }
        )
    result.append(
        {
            "name": "Knowledge Base",
            "mode": "live",
            "detail": "Workspace-scoped hybrid search"
            if settings.embedding_model
            else "Workspace-scoped keyword search; configure embeddings for hybrid search",
        }
    )
    return result
