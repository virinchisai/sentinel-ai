"""Security regression tests — every defense must stay turned on."""

from __future__ import annotations

import pytest

from backend.auth.jwt import create_access_token, verify_token
from backend.auth.password import PasswordError, validate_password
from backend.auth.rbac import has_permission
from backend.auth.models import Role
from backend.mcp_server.connectors.database_client import get_client as db_client
from backend.mcp_server.connectors.filesystem_client import get_client as fs_client


# ─── Passwords ───

def test_password_rejects_too_short():
    with pytest.raises(PasswordError, match="at least"):
        validate_password("abc1!")


def test_password_rejects_common():
    with pytest.raises(PasswordError, match="common"):
        validate_password("password")


def test_password_rejects_letter_only():
    with pytest.raises(PasswordError, match="digit or special"):
        validate_password("abcdefghij")


def test_password_accepts_strong():
    validate_password("StrongP@ss123")


# ─── JWT ───

def test_jwt_round_trip():
    token = create_access_token({"sub": "alice", "role": "user"})
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "alice"


def test_jwt_rejects_tampered():
    token = create_access_token({"sub": "alice"})
    tampered = token[:-3] + "xxx"
    assert verify_token(tampered) is None


def test_jwt_rejects_wrong_type():
    token = create_access_token({"sub": "alice"})
    # access token presented when a refresh token was expected
    assert verify_token(token, expected_type="refresh") is None


# ─── RBAC ───

def test_rbac_admin_has_manage_users():
    assert has_permission(Role.ADMIN, "manage_users")


def test_rbac_user_blocked_from_manage_users():
    assert not has_permission(Role.USER, "manage_users")


def test_rbac_viewer_blocked_from_uploads():
    assert not has_permission(Role.VIEWER, "upload_documents")


# ─── Database connector ───

def test_db_blocks_drop():
    r = db_client().execute_query("DROP TABLE employees")
    assert "error" in r and "SELECT" in r["error"]


def test_db_blocks_delete():
    r = db_client().execute_query("DELETE FROM employees")
    assert "error" in r


def test_db_blocks_insert():
    r = db_client().execute_query("INSERT INTO employees (name) VALUES ('x')")
    assert "error" in r


def test_db_allows_select():
    r = db_client().execute_query("SELECT name FROM employees LIMIT 1")
    assert "rows" in r and len(r["rows"]) >= 1


# ─── File system sandbox ───

def test_fs_blocks_path_traversal():
    with pytest.raises(PermissionError):
        fs_client()._safe_path("../../../etc/passwd")


def test_fs_blocks_absolute_escape():
    with pytest.raises(PermissionError):
        fs_client()._safe_path("/etc/passwd")
