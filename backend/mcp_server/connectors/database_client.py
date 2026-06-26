"""PostgreSQL connector for read-only SQL queries and schema introspection.

Uses SQLite as a fallback in demo mode when no PostgreSQL URL is configured.
"""

from __future__ import annotations

import sqlite3

from backend.config import settings

DEMO_DB = "sentinel_demo.db"


def _init_demo_db() -> None:
    """Create a small demo database with sample enterprise data."""
    conn = sqlite3.connect(DEMO_DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            title TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            salary REAL NOT NULL
        );
        INSERT OR IGNORE INTO employees VALUES (1, 'Alice Chen', 'Engineering', 'Staff Engineer', '2021-03-15', 185000);
        INSERT OR IGNORE INTO employees VALUES (2, 'Bob Martinez', 'Engineering', 'Senior Engineer', '2022-06-01', 165000);
        INSERT OR IGNORE INTO employees VALUES (3, 'Carol Smith', 'Product', 'Product Manager', '2021-09-20', 155000);
        INSERT OR IGNORE INTO employees VALUES (4, 'David Kim', 'Engineering', 'Engineer', '2023-01-10', 140000);
        INSERT OR IGNORE INTO employees VALUES (5, 'Eva Johnson', 'Data Science', 'Data Scientist', '2022-11-05', 160000);

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            lead_id INTEGER REFERENCES employees(id),
            start_date TEXT NOT NULL
        );
        INSERT OR IGNORE INTO projects VALUES (1, 'Auth Service Migration', 'in_progress', 1, '2025-04-01');
        INSERT OR IGNORE INTO projects VALUES (2, 'ML Pipeline v2', 'planning', 5, '2025-07-01');
        INSERT OR IGNORE INTO projects VALUES (3, 'Mobile App Redesign', 'in_progress', 3, '2025-03-15');
    """)
    conn.commit()
    conn.close()


class DatabaseClient:
    def __init__(self) -> None:
        self._use_demo = settings.database_url.startswith("sqlite")
        if self._use_demo:
            _init_demo_db()

    def execute_query(self, sql: str) -> dict:
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return {"error": "Only SELECT queries are allowed (read-only)"}

        try:
            if self._use_demo:
                conn = sqlite3.connect(DEMO_DB)
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = [dict(row) for row in cursor.fetchall()[:100]]
                conn.close()
                return {"columns": columns, "rows": rows, "row_count": len(rows)}
            else:
                import psycopg2
                import psycopg2.extras

                conn = psycopg2.connect(settings.database_url)
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = [dict(row) for row in cursor.fetchall()[:100]]
                cursor.close()
                conn.close()
                return {"columns": columns, "rows": rows, "row_count": len(rows)}
        except Exception as e:
            return {"error": str(e)}

    def describe_schema(self) -> list[dict]:
        if self._use_demo:
            conn = sqlite3.connect(DEMO_DB)
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            schema = []
            for (table_name,) in tables:
                cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                schema.append({
                    "table": table_name,
                    "columns": [{"name": c[1], "type": c[2], "nullable": not c[3]} for c in cols],
                })
            conn.close()
            return schema
        return []


_client: DatabaseClient | None = None


def get_client() -> DatabaseClient:
    global _client
    if _client is None:
        _client = DatabaseClient()
    return _client
