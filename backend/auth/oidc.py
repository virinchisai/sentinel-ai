"""Optional Keycloak/OIDC authorization-code exchange with PKCE."""

import hashlib
import httpx
import jwt
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from backend.config import settings
from backend.auth.models import User, Role, get_db
from backend.auth.jwt import create_access_token, create_refresh_token
from backend.auth.audit import log_action

router = APIRouter(prefix="/auth/sso", tags=["auth"])


@router.get("/config")
def config():
    if not settings.oidc_issuer or not settings.oidc_client_id:
        return {"enabled": False}
    return {
        "enabled": True,
        "authorization_endpoint": settings.oidc_issuer.rstrip("/")
        + "/protocol/openid-connect/auth",
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
    }


class Exchange(BaseModel):
    code: str = Field(min_length=1, max_length=4000)
    code_verifier: str = Field(min_length=43, max_length=128)
    nonce: str = Field(min_length=20, max_length=128)


@router.post("/exchange")
def exchange(body: Exchange, db=Depends(get_db)):
    if not config()["enabled"]:
        raise HTTPException(404, "SSO is disabled")
    issuer = settings.oidc_issuer.rstrip("/")
    try:
        with httpx.Client(timeout=15) as client:
            response = client.post(
                issuer + "/protocol/openid-connect/token",
                data={
                    "grant_type": "authorization_code",
                    "code": body.code,
                    "client_id": settings.oidc_client_id,
                    "redirect_uri": settings.oidc_redirect_uri,
                    "code_verifier": body.code_verifier,
                },
            )
            response.raise_for_status()
            token = response.json()["id_token"]
            keys = client.get(issuer + "/protocol/openid-connect/certs")
            keys.raise_for_status()
        header = jwt.get_unverified_header(token)
        raw = next(k for k in keys.json()["keys"] if k["kid"] == header["kid"])
        key = jwt.PyJWK.from_dict(raw, algorithm="RS256").key
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.oidc_client_id,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub", "nonce"]},
        )
        if claims["nonce"] != body.nonce:
            raise ValueError("Invalid nonce")
    except Exception:
        raise HTTPException(401, "SSO verification failed")
    # Stable issuer+subject binding; never auto-link by a claimed email address.
    identifier = hashlib.sha256((issuer + "|" + claims["sub"]).encode()).hexdigest()
    username = "sso-" + identifier[:40]
    user = db.query(User).filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=identifier + "@sso.invalid",
            hashed_password="!disabled",
            role=Role.USER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    log_action(user.id, "sso.login")
    return {
        "access_token": create_access_token(
            {"sub": user.username, "ver": user.token_version, "role": user.role.value}
        ),
        "refresh_token": create_refresh_token(
            {"sub": user.username, "ver": user.token_version}
        ),
        "token_type": "bearer",
    }
