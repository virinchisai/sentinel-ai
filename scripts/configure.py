"""Create private local configuration once, without printing secrets."""

from pathlib import Path
import secrets
import os

root = Path(__file__).resolve().parents[1]
path = root / ".env"
if path.exists():
    raise SystemExit(".env already exists; leaving it unchanged")
content = (
    (root / ".env.example")
    .read_text()
    .replace("JWT_SECRET_KEY=\n", "JWT_SECRET_KEY=" + secrets.token_urlsafe(48) + "\n")
    .replace(
        "POSTGRES_PASSWORD=\n", "POSTGRES_PASSWORD=" + secrets.token_hex(24) + "\n"
    )
)
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as file:
    file.write(content)
print("Created .env with generated secrets. No secrets were printed.")
