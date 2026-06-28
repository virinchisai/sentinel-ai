"""Auth API routes: register, login, refresh, me."""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from backend.auth.audit import log_action
from backend.auth.jwt import create_access_token, create_refresh_token, verify_token
from backend.auth.middleware import get_current_user, security
from backend.auth.models import Role, User, get_db
from backend.auth.password import PasswordError, validate_password
from backend.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory token revocation set; in production this would be Redis.
_revoked_tokens: set[str] = set()
_revoked_token_ids: set[str] = set()


def is_revoked(token: str, payload: dict | None = None) -> bool:
    payload = payload or verify_token(token) or verify_token(token, expected_type="refresh")
    token_id = payload.get("jti") if payload else None
    return token in _revoked_tokens or bool(token_id and token_id in _revoked_token_ids)


def revoke(token: str, payload: dict | None = None) -> None:
    _revoked_tokens.add(token)
    payload = payload or verify_token(token) or verify_token(token, expected_type="refresh")
    token_id = payload.get("jti") if payload else None
    if token_id:
        _revoked_token_ids.add(token_id)


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    authenticated: bool = True
    token_type: str = "cookie"


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(settings.access_cookie_name, access_token, **cookie_kwargs)
    response.set_cookie(settings.refresh_cookie_name, refresh_token, **cookie_kwargs)


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.access_cookie_name, path="/")
    response.delete_cookie(settings.refresh_cookie_name, path="/")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, req: RegisterRequest, db=Depends(get_db)):
    try:
        validate_password(req.password)
    except PasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if db.query(User).filter((User.username == req.username) | (User.email == req.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=pwd_context.hash(req.password),
        role=Role.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(user.id, "register")
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, response: Response, db=Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.username, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.username})
    _set_auth_cookies(response, access_token, refresh_token)
    log_action(user.id, "login")
    return TokenResponse()


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    req: RefreshRequest | None = None,
    refresh_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
    db=Depends(get_db),
):
    refresh_token = (req.refresh_token if req else None) or refresh_cookie
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = verify_token(refresh_token, expected_type="refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if is_revoked(refresh_token, payload):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    revoke(refresh_token, payload)
    access_token = create_access_token({"sub": user.username, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.username})
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse()


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    credentials=Depends(security),
    user: User = Depends(get_current_user),
    access_cookie: str | None = Cookie(default=None, alias=settings.access_cookie_name),
    refresh_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
):
    """Revoke the current access token. Subsequent calls with it will 401."""
    access_token = credentials.credentials if credentials else access_cookie
    if access_token:
        revoke(access_token)
    if refresh_cookie:
        revoke(refresh_cookie)
    _clear_auth_cookies(response)
    log_action(user.id, "logout")
