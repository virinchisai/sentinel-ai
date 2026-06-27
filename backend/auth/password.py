"""Password strength validation."""

from __future__ import annotations

import re

MIN_LENGTH = 8
COMMON_PASSWORDS = {
    "password", "12345678", "qwerty", "admin", "letmein",
    "welcome", "monkey", "dragon", "master", "abc12345",
    "password1", "iloveyou", "sentinel-ai",
}


class PasswordError(ValueError):
    pass


def validate_password(password: str) -> None:
    """Raise PasswordError if the password doesn't meet policy.

    Policy:
      - >= 8 chars
      - at least one letter and one digit OR special char
      - not in the common-password list
    """
    if len(password) < MIN_LENGTH:
        raise PasswordError(f"Password must be at least {MIN_LENGTH} characters")

    if password.lower() in COMMON_PASSWORDS:
        raise PasswordError("Password is too common — pick something less guessable")

    has_letter = bool(re.search(r"[A-Za-z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[^A-Za-z0-9]", password))

    if not has_letter:
        raise PasswordError("Password must contain at least one letter")

    if not (has_digit or has_special):
        raise PasswordError("Password must contain a digit or special character")
