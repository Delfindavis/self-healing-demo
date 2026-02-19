import sqlite3
import csv
from db import calculate_uptime

def export_checks(db_name="monitor.db", csv_file="checks.csv"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT * FROM checks')
    rows = c.fetchall()
    conn.close()
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Status', 'OK'])
        writer.writerows(rows)

def export_restarts(db_name="monitor.db", csv_file="restarts.csv"):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('SELECT * FROM restarts')
    rows = c.fetchall()
    conn.close()
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Reason'])
        writer.writerows(rows)

# Optional: export uptime report
uptime = calculate_uptime()
with open("uptime_report.txt", "w") as f:
    f.write(f"Current uptime: {uptime:.2f}%\n")

export_checks()
export_restarts()
print("CSV & uptime report exported!")
