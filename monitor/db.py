import sqlite3
from pathlib import Path

DB_NAME = str(Path(__file__).resolve().parent / "monitor.db")


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            ts TEXT,
            service TEXT,
            status INTEGER,
            ok INTEGER,
            failure_type TEXT
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

    conn.commit()
    conn.close()


def log_check(ts, service, status, ok, failure_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO checks VALUES (?,?,?,?,?)',
              (ts, service, status, ok, failure_type))
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