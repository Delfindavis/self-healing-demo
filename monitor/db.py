import sqlite3

DB_NAME = "monitor.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table to log each health check
    c.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            ts TEXT,
            status INTEGER,
            ok INTEGER
        )
    ''')
    # Table to log container restarts
    c.execute('''
        CREATE TABLE IF NOT EXISTS restarts (
            ts TEXT,
            reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_check(ts, status, ok):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO checks VALUES (?,?,?)', (ts, status, ok))
    conn.commit()
    conn.close()

def log_restart(ts, reason):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO restarts VALUES (?,?)', (ts, reason))
    conn.commit()
    conn.close()
