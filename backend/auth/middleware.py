"""FastAPI dependencies for JWT auth and RBAC enforcement."""

from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.jwt import verify_token
from backend.auth.models import Role, User, get_db
from backend.auth.rbac import has_permission
from backend.config import settings

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    access_cookie: str | None = Cookie(default=None, alias=settings.access_cookie_name),
    db=Depends(get_db),
) -> User:
    # avoid circular import: routes imports middleware
    from backend.auth.routes import is_revoked

    token = credentials.credentials if credentials else access_cookie
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if is_revoked(token, payload):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_permission(permission: str):
    def checker(user: User = Depends(get_current_user)):
        if not has_permission(user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return user

    return checker
