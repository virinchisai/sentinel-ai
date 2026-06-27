#!/usr/bin/env bash
set -euo pipefail

echo "→ Installing Python dependencies (this takes ~3 minutes)..."
pip install --upgrade pip
pip install -e ".[dev]"

echo "→ Installing frontend dependencies..."
cd frontend
npm ci
cd ..

echo "→ Ingesting sample knowledge base..."
python -m backend.rag.ingest || echo "  (skipped — will run on first chat)"

echo "→ Seeding a demo user (alice / sentinel-demo)..."
python -c "
from backend.auth.models import init_db, User, Role, get_session_factory
from passlib.context import CryptContext
init_db()
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = get_session_factory()()
if not db.query(User).filter(User.username=='alice').first():
    db.add(User(username='alice', email='alice@demo.com',
                hashed_password=pwd.hash('sentinel-demo'), role=Role.USER))
    db.commit()
    print('  Created demo user: alice / sentinel-demo')
else:
    print('  Demo user already exists.')
db.close()
"

echo
echo "✅ Setup complete."
echo
echo "═══════════════════════════════════════════════════════════════"
echo "  SentinelAI is ready."
echo "  Demo login → username: alice   password: sentinel-demo"
echo "  Run both servers:    bash .devcontainer/start.sh"
echo "═══════════════════════════════════════════════════════════════"
