import time
import requests
import subprocess
from datetime import datetime

try:
    from monitor.email_alert import send_email
    from monitor.db import init_db, log_check, log_restart
    from monitor.uptime import calculate_uptime
except ModuleNotFoundError:
    from email_alert import send_email
    from db import init_db, log_check, log_restart
    from uptime import calculate_uptime

# ── Config ───────────────────────────────────────────────
FAILURE_THRESHOLD = 3
MAX_RESTARTS      = 3
CHECK_INTERVAL    = 10
RESTART_GRACE     = 20
# ────────────────────────────────────────────────────────

SERVICES = {
    "webapp-main":    "http://localhost:5000/health",
    "webapp-auth":    "http://localhost:5001/health",
    "webapp-payment": "http://localhost:5002/health"
}

failures       = { s: 0     for s in SERVICES }
restart_counts = { s: 0     for s in SERVICES }
restart_time   = { s: None  for s in SERVICES }
alerted        = { s: False for s in SERVICES }

check_count = 0
init_db()


def get_container_name(service):
    """Find the actual Docker container name for a service."""
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    for name in result.stdout.strip().split("\n"):
        if service in name:
            return name.strip()
    return service  # fallback


def restart_container(service, reason):
    ts        = datetime.now().isoformat()
    attempt   = restart_counts[service] + 1
    container = get_container_name(service)

    print(f"\n  [RESTART] {service} → container: {container}")
    print(f"  [RESTART] Reason: {reason} | Attempt {attempt}/{MAX_RESTARTS}")

    result = subprocess.run(
        ["docker", "restart", container],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"  [RESTART] Success! Waiting {RESTART_GRACE}s grace period...")
        restart_time[service] = time.time()
    else:
        print(f"  [RESTART] Failed: {result.stderr.strip()}")

    log_restart(ts, service, reason)


def is_container_running(service):
    container = get_container_name(service)
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "true"


def in_grace_period(service):
    if restart_time[service] is None:
        return False
    elapsed = time.time() - restart_time[service]
    if elapsed < RESTART_GRACE:
        remaining = int(RESTART_GRACE - elapsed)
        print(f"  [GRACE] {service} — booting up ({remaining}s left), skipping check")
        return True
    restart_time[service] = None
    return False


# ── Startup ──────────────────────────────────────────────
print("=" * 50)
print("  Self-Healing Monitor — STARTED")
print(f"  Failure Threshold : {FAILURE_THRESHOLD}")
print(f"  Max Restarts      : {MAX_RESTARTS}")
print(f"  Check Interval    : {CHECK_INTERVAL}s")
print(f"  Restart Grace     : {RESTART_GRACE}s")
print()

# Show detected container names on startup
print("  Detected containers:")
for svc in SERVICES:
    c = get_container_name(svc)
    print(f"    {svc} → {c}")
print("=" * 50)


while True:
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{now}] Checking services...")

    for service, url in SERVICES.items():

        if in_grace_period(service):
            continue

        timestamp    = datetime.now().isoformat()
        status_code  = 0
        success      = 0
        failure_type = "NONE"

        try:
            response    = requests.get(url, timeout=3)
            status_code = response.status_code

            if response.status_code == 200:
                print(f"  [UP]  {service}")
                failures[service]       = 0
                restart_counts[service] = 0
                alerted[service]        = False
                success = 1
            else:
                failure_type = "HTTP_ERROR"
                failures[service] += 1
                print(f"  [ERR] {service} → HTTP {response.status_code}  ({failures[service]}/{FAILURE_THRESHOLD})")

        except requests.exceptions.Timeout:
            failure_type = "TIMEOUT"
            failures[service] += 1
            print(f"  [ERR] {service} → TIMEOUT  ({failures[service]}/{FAILURE_THRESHOLD})")

        except requests.exceptions.ConnectionError:
            if not is_container_running(service):
                failure_type = "CONTAINER_STOPPED"
                print(f"  [ERR] {service} → CONTAINER STOPPED  ({failures[service]+1}/{FAILURE_THRESHOLD})")
            else:
                failure_type = "NETWORK_ERROR"
                print(f"  [ERR] {service} → NETWORK ERROR  ({failures[service]+1}/{FAILURE_THRESHOLD})")
            failures[service] += 1

        except Exception as e:
            failure_type = "UNKNOWN_ERROR"
            failures[service] += 1
            print(f"  [ERR] {service} → {e}  ({failures[service]}/{FAILURE_THRESHOLD})")

        log_check(timestamp, service, status_code, success, failure_type)

        # ── Self-Healing ──────────────────────────────────────
        if failures[service] >= FAILURE_THRESHOLD:
            failures[service] = 0

            if restart_counts[service] < MAX_RESTARTS:
                restart_container(service, failure_type)
                restart_counts[service] += 1
            else:
                if not alerted[service]:
                    print(f"\n  [ALERT] {service} — max restarts exceeded! Sending email...")
                    send_email(service, f"Max restarts exceeded — {failure_type}")
                    alerted[service] = True
                else:
                    print(f"  [ALERT] {service} still down — manual intervention required")
        # ─────────────────────────────────────────────────────

    check_count += 1

    if check_count % 10 == 0:
        print("\n  ── Uptime Report ──")
        for svc in SERVICES:
            print(f"    {svc}: {calculate_uptime(svc):.1f}%")
        print(f"    Overall: {calculate_uptime():.1f}%")
        print("  ──────────────────")

    time.sleep(CHECK_INTERVAL)