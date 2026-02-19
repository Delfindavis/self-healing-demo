import sqlite3

def calculate_uptime(db_name="monitor.db"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM checks')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM checks WHERE ok=1')
    up = c.fetchone()[0]
    conn.close()
    if total == 0:
        return 0
    return (up / total) * 100
