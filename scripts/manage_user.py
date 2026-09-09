"""Local operator-only role management; requires direct deployment DB access."""

import argparse
from backend.auth.models import User, Role, get_session_factory
from backend.auth.audit import log_action
from backend.migrate import migrate

parser = argparse.ArgumentParser()
parser.add_argument("username")
parser.add_argument("role", choices=[r.value for r in Role])
args = parser.parse_args()
migrate()
with get_session_factory()() as db:
    user = db.query(User).filter_by(username=args.username).first()
    if not user:
        raise SystemExit("User not found")
    user.role = Role(args.role)
    user.token_version += 1
    db.commit()
    log_action(user.id, "operator.role.change", args.username, args.role)
print("Role updated; existing sessions revoked.")
