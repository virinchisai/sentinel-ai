"""Consistent SQLite backup and verified restore into a NEW destination.

For PostgreSQL use pg_dump/pg_restore; see docs/operations.md.
"""

import argparse
import sqlite3
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("source", type=Path)
p.add_argument("destination", type=Path)
a = p.parse_args()
if not a.source.is_file() or a.destination.exists():
    raise SystemExit("Source must exist and destination must not exist")
with sqlite3.connect(f"file:{a.source.resolve()}?mode=ro", uri=True) as source:
    with sqlite3.connect(a.destination) as target:
        source.backup(target)
        if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit("Integrity verification failed")
print("Copy completed; SQLite integrity check passed.")
