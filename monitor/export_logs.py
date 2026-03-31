import sqlite3
import csv
from pathlib import Path

try:
    from monitor.uptime import calculate_uptime
except ModuleNotFoundError:
    from uptime import calculate_uptime

BASE_DIR = Path(__file__).resolve().parent


def export_checks(db_name=BASE_DIR / "monitor.db", csv_file=BASE_DIR / "checks.csv"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT * FROM checks')
    rows = c.fetchall()
    conn.close()
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Service', 'Status', 'OK', 'FailureType'])
        writer.writerows(rows)
    print(f"Exported {len(rows)} checks to {csv_file}")


def export_restarts(db_name=BASE_DIR / "monitor.db", csv_file=BASE_DIR / "restarts.csv"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT * FROM restarts')
    rows = c.fetchall()
    conn.close()
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Service', 'Reason'])
        writer.writerows(rows)
    print(f"Exported {len(rows)} restarts to {csv_file}")


def export_email_logs(db_name=BASE_DIR / "monitor.db", csv_file=BASE_DIR / "email_logs.csv"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT * FROM email_logs')
    rows = c.fetchall()
    conn.close()
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Service', 'Reason', 'Recipient', 'Status'])
        writer.writerows(rows)
    print(f"Exported {len(rows)} email logs to {csv_file}")


def export_uptime():
    services = ["webapp-main", "webapp-auth", "webapp-payment"]
    with open(BASE_DIR / "uptime_report.txt", "w") as f:
        for svc in services:
            u = calculate_uptime(svc)
            f.write(f"{svc}: {u:.2f}%\n")
        overall = calculate_uptime()
        f.write(f"\nOverall Uptime: {overall:.2f}%\n")
    print("Uptime report exported to uptime_report.txt")


if __name__ == "__main__":
    export_checks()
    export_restarts()
    export_email_logs()
    export_uptime()
    print("\nAll logs exported successfully!")