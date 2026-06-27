"""Auth API routes: register, login, refresh, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
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

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory token revocation set; in production this would be Redis.
_revoked_tokens: set[str] = set()


def is_revoked(token: str) -> bool:
    return token in _revoked_tokens


def revoke(token: str) -> None:
    _revoked_tokens.add(token)


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


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
def login(request: Request, req: LoginRequest, db=Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.username, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.username})
    log_action(user.id, "login")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, db=Depends(get_db)):
    payload = verify_token(req.refresh_token, expected_type="refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": user.username, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.username})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(
    credentials=Depends(security),
    user: User = Depends(get_current_user),
):
    """Revoke the current access token. Subsequent calls with it will 401."""
    revoke(credentials.credentials)
    log_action(user.id, "logout")
