"""Auth API routes: register, login, refresh, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
import bcrypt
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from backend.auth.audit import log_action
from backend.auth.jwt import create_access_token, create_refresh_token, verify_token
from backend.auth.middleware import get_current_user, security
from backend.auth.models import Role, User, UsedRefresh, get_db
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from backend.auth.password import PasswordError, validate_password

router = APIRouter(prefix="/auth", tags=["auth"])


class PasswordHasher:
    @staticmethod
    def hash(password):
        if len(password.encode()) > 72:
            raise HTTPException(400, "Password must be at most 72 UTF-8 bytes")
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify(password, hashed):
        if len(password.encode()) > 72:
            return False
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except ValueError:
            return False


pwd_context = PasswordHasher()


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    password: str = Field(max_length=72)


class LoginRequest(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=72)


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

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def register(request: Request, req: RegisterRequest, db=Depends(get_db)):
    if req.username.startswith(("sso-", "benchmark-")):
        raise HTTPException(400, "Reserved username prefix")
    try:
        validate_password(req.password)
    except PasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if (
        db.query(User)
        .filter((User.username == req.username) | (User.email == req.email))
        .first()
    ):
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
    if (
        not user
        or user.hashed_password.startswith("!")
        or not pwd_context.verify(req.password, user.hashed_password)
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        {"sub": user.username, "role": user.role.value, "ver": user.token_version}
    )
    refresh_token = create_refresh_token(
        {"sub": user.username, "ver": user.token_version}
    )
    log_action(user.id, "login")
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, db=Depends(get_db)):
    payload = verify_token(req.refresh_token, expected_type="refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user or payload.get("ver", -1) != user.token_version:
        raise HTTPException(status_code=401, detail="Session revoked")
    try:
        db.add(
            UsedRefresh(
                jti=payload["jti"],
                expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc),
            )
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=401, detail="Refresh token already used")

    access_token = create_access_token(
        {"sub": user.username, "role": user.role.value, "ver": user.token_version}
    )
    refresh_token = create_refresh_token(
        {"sub": user.username, "ver": user.token_version}
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(
    credentials=Depends(security),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Revoke the current access token. Subsequent calls with it will 401."""
    db.query(User).filter_by(id=user.id).update(
        {"token_version": User.token_version + 1}
    )
    db.commit()
    log_action(user.id, "logout")
