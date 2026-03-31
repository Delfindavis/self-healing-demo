import sqlite3
from pathlib import Path

DB_NAME = str(Path(__file__).resolve().parent / "monitor.db")


def calculate_uptime(service=None):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        if service:
            c.execute("SELECT COUNT(*) FROM checks WHERE service=?", (service,))
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM checks WHERE service=? AND ok=1", (service,))
            success = c.fetchone()[0]
        else:
            c.execute("SELECT COUNT(*) FROM checks")
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM checks WHERE ok=1")
            success = c.fetchone()[0]

        conn.close()

        if total == 0:
            return 0.0

        return round((success / total) * 100, 2)

    except Exception as e:
        print(f"Uptime calculation error: {e}")
        return 0.0