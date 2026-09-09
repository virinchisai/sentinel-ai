"""Deterministic retrieval release gate; no model judge or paid API required."""

import json
import time
from pathlib import Path
from backend.auth.models import User, Role, get_session_factory
from backend.migrate import migrate
from backend.auth.workspaces import resolve_workspace
from backend.rag.ingest import ingest
from backend.rag.documents import retrieve

cases = [
    ("paid time off carryover", "pto_policy.md"),
    ("expense reimbursement receipt", "expense_policy.md"),
    ("incident severity response", "incident_response.md"),
    ("password security requirements", "security_policy.md"),
    ("engineering code review", "engineering_standards.md"),
    ("onboarding new employee", "onboarding_faq.md"),
]


def main():
    migrate()
    with get_session_factory()() as db:
        user = db.query(User).filter_by(username="benchmark-service").first()
        if not user:
            user = User(
                username="benchmark-service",
                email="benchmark@example.invalid",
                hashed_password="!disabled",
                role=Role.VIEWER,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        uid = user.id
    workspace = resolve_workspace(uid)
    ingest(user_id=uid, workspace_id=workspace)
    results = []
    for query, expected in cases:
        start = time.perf_counter()
        hits = retrieve(query, workspace, 3)
        results.append(
            {
                "query": query,
                "expected": expected,
                "sources": [h["source"] for h in hits],
                "hit_at_3": any(h["source"] == expected for h in hits),
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        )
    report = {
        "cases": results,
        "hit_at_3": sum(r["hit_at_3"] for r in results) / len(results),
        "scope": "Deterministic sample-document retrieval; not a production accuracy claim",
    }
    path = Path("evaluation/results/benchmark.json")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if report["hit_at_3"] < 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
