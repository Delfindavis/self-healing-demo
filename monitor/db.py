import sqlite3
from pathlib import Path

DB_NAME = str(Path(__file__).resolve().parent / "monitor.db")


def _ensure_column(conn, table, column, column_type):
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in c.fetchall()}
    if column not in existing:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            ts TEXT,
            service TEXT,
            status INTEGER,
            ok INTEGER,
            failure_type TEXT,
            response_ms REAL DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS restarts (
            ts TEXT,
            service TEXT,
            reason TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            ts TEXT,
            service TEXT,
            reason TEXT,
            recipient TEXT,
            status TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS recovery_actions (
            ts TEXT,
            service TEXT,
            failure_type TEXT,
            action TEXT,
            result TEXT,
            details TEXT
        )
    ''')

    # Lightweight migration for old DBs created before response_ms was added.
    _ensure_column(conn, "checks", "response_ms", "REAL DEFAULT 0")

    conn.commit()
    conn.close()


def log_check(ts, service, status, ok, failure_type, response_ms=0.0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO checks (ts, service, status, ok, failure_type, response_ms) VALUES (?,?,?,?,?,?)',
              (ts, service, status, ok, failure_type, float(response_ms or 0.0)))
    conn.commit()
    conn.close()


def log_restart(ts, service, reason):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO restarts VALUES (?,?,?)',
              (ts, service, reason))
    conn.commit()
    conn.close()


def log_email(ts, service, reason, recipient, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO email_logs VALUES (?,?,?,?,?)',
              (ts, service, reason, recipient, status))
    conn.commit()
    conn.close()


def log_recovery_action(ts, service, failure_type, action, result, details):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        'INSERT INTO recovery_actions VALUES (?,?,?,?,?,?)',
        (ts, service, failure_type, action, result, details),
    )
    conn.commit()
    conn.close()