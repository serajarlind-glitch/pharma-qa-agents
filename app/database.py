"""
SQLite database for pharma QA run history and audit trails.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "pharma_qa.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def db_session():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db_session() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                workflow_name TEXT NOT NULL,
                variables TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                precision_mode INTEGER DEFAULT 0,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                total_elapsed REAL,
                final_output TEXT,
                summary TEXT,
                audit_trail TEXT
            );

            CREATE TABLE IF NOT EXISTS run_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                agent_role TEXT NOT NULL,
                output TEXT,
                elapsed_seconds REAL,
                success INTEGER DEFAULT 1,
                error TEXT,
                review_score INTEGER,
                review_decision TEXT,
                structured_data TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            );

            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_role TEXT NOT NULL,
                user_message TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_runs_workflow ON runs(workflow_name);
            CREATE INDEX IF NOT EXISTS idx_runs_started ON runs(started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_steps_run ON run_steps(run_id);
            CREATE INDEX IF NOT EXISTS idx_chats_agent ON chats(agent_role);
        """)


def create_run(workflow_name: str, variables: dict, precision: bool) -> str:
    run_id = str(uuid.uuid4())[:12]
    with db_session() as conn:
        conn.execute(
            "INSERT INTO runs (id, workflow_name, variables, precision_mode, started_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (run_id, workflow_name, json.dumps(variables), int(precision),
             datetime.now(timezone.utc).isoformat()),
        )
    return run_id


def add_step(run_id: str, step_name: str, agent_role: str, output: str,
             elapsed: float, success: bool, error: str = None,
             review_score: int = None, review_decision: str = None,
             structured_data: dict = None):
    with db_session() as conn:
        conn.execute(
            "INSERT INTO run_steps (run_id, step_name, agent_role, output, "
            "elapsed_seconds, success, error, review_score, review_decision, "
            "structured_data, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, step_name, agent_role, output, elapsed, int(success),
             error, review_score, review_decision,
             json.dumps(structured_data) if structured_data else None,
             datetime.now(timezone.utc).isoformat()),
        )


def complete_run(run_id: str, status: str, total_elapsed: float,
                 final_output: str, summary: str, audit_trail: str = None):
    with db_session() as conn:
        conn.execute(
            "UPDATE runs SET status=?, completed_at=?, total_elapsed=?, "
            "final_output=?, summary=?, audit_trail=? WHERE id=?",
            (status, datetime.now(timezone.utc).isoformat(), total_elapsed,
             final_output, summary, audit_trail, run_id),
        )


def get_runs(limit: int = 50):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_run(run_id: str):
    with db_session() as conn:
        run = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if not run:
            return None
        steps = conn.execute(
            "SELECT * FROM run_steps WHERE run_id=? ORDER BY id", (run_id,)
        ).fetchall()
    return {"run": dict(run), "steps": [dict(s) for s in steps]}


def save_chat(agent_role: str, user_message: str, agent_response: str):
    with db_session() as conn:
        conn.execute(
            "INSERT INTO chats (agent_role, user_message, agent_response, created_at) "
            "VALUES (?, ?, ?, ?)",
            (agent_role, user_message, agent_response,
             datetime.now(timezone.utc).isoformat()),
        )


def get_chat_history(agent_role: str, limit: int = 20):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM chats WHERE agent_role=? ORDER BY id DESC LIMIT ?",
            (agent_role, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_stats():
    with db_session() as conn:
        total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        completed = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE status='completed'"
        ).fetchone()[0]
        precision = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE precision_mode=1"
        ).fetchone()[0]
        avg_time = conn.execute(
            "SELECT AVG(total_elapsed) FROM runs WHERE status='completed'"
        ).fetchone()[0]
    return {
        "total_runs": total,
        "completed": completed,
        "precision_runs": precision,
        "avg_time": round(avg_time or 0, 1),
    }
