import time
import requests
import subprocess
from datetime import datetime

try:
    from monitor.email_alert import send_email
    from monitor.db import init_db, log_check, log_restart, log_recovery_action
    from monitor.uptime import calculate_uptime
except ModuleNotFoundError:
    from email_alert import send_email
    from db import init_db, log_check, log_restart, log_recovery_action
    from uptime import calculate_uptime

# -- Config ------------------------------------------------
FAILURE_THRESHOLD = 3
MAX_RESTARTS = 3
CHECK_INTERVAL = 10
RESTART_GRACE = 20
REQUEST_TIMEOUT = 3
# ---------------------------------------------------------

SERVICES = {
    "webapp-main": "http://localhost:5000/health",
    "webapp-auth": "http://localhost:5001/health",
    "webapp-payment": "http://localhost:5002/health",
}

failures = {svc: 0 for svc in SERVICES}
restart_counts = {svc: 0 for svc in SERVICES}
restart_time = {svc: None for svc in SERVICES}
alerted = {svc: False for svc in SERVICES}

check_count = 0
init_db()


def run_cmd(command):
    return subprocess.run(command, capture_output=True, text=True)


def get_container_name(service, running_only=False):
    """Find Docker container name for a service."""
    cmd = ["docker", "ps", "--format", "{{.Names}}"]
    if not running_only:
        cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]

    result = run_cmd(cmd)
    if result.returncode != 0:
        return service

    names = [name.strip() for name in result.stdout.strip().split("\n") if name.strip()]
    for name in names:
        if name == service or name.endswith(f"_{service}_1"):
            return name
    for name in names:
        if service in name:
            return name
    return service


def get_network_name():
    """Detect compose network name dynamically."""
    result = run_cmd(["docker", "network", "ls", "--format", "{{.Name}}"])
    if result.returncode != 0:
        return "self-healing-demo_default"

    for name in result.stdout.strip().split("\n"):
        n = name.strip()
        if n and "self-healing-demo" in n.lower():
            return n
    for name in result.stdout.strip().split("\n"):
        n = name.strip()
        if n and "self-healing" in n.lower():
            return n
    return "self-healing-demo_default"


def is_container_running(service):
    container = get_container_name(service, running_only=False)
    result = run_cmd(["docker", "inspect", "-f", "{{.State.Running}}", container])
    return result.returncode == 0 and result.stdout.strip() == "true"


def in_grace_period(service):
    if restart_time[service] is None:
        return False
    elapsed = time.time() - restart_time[service]
    if elapsed < RESTART_GRACE:
        remaining = int(RESTART_GRACE - elapsed)
        print(f"  [GRACE] {service} - booting up ({remaining}s left), skipping check")
        return True
    restart_time[service] = None
    return False


def restart_container(service, reason):
    ts = datetime.now().isoformat()
    attempt = restart_counts[service] + 1
    container = get_container_name(service)

    print(f"\n  [RESTART] {service} -> container: {container}")
    print(f"  [RESTART] Reason: {reason} | Attempt {attempt}/{MAX_RESTARTS}")

    result = run_cmd(["docker", "restart", container])
    ok = result.returncode == 0
    details = result.stdout.strip() if ok else result.stderr.strip()

    if ok:
        print(f"  [RESTART] Success! Waiting {RESTART_GRACE}s grace period...")
        restart_time[service] = time.time()
        log_restart(ts, service, reason)
        log_recovery_action(ts, service, reason, "restart_container", "SUCCESS", details)
    else:
        print(f"  [RESTART] Failed: {details}")
        log_recovery_action(ts, service, reason, "restart_container", "FAILED", details)

    return ok


def start_container(service, reason):
    ts = datetime.now().isoformat()
    container = get_container_name(service, running_only=False)
    result = run_cmd(["docker", "start", container])
    ok = result.returncode == 0
    details = result.stdout.strip() if ok else result.stderr.strip()

    if ok:
        print(f"  [RECOVERY] Started {container}. Waiting {RESTART_GRACE}s...")
        restart_time[service] = time.time()
    else:
        print(f"  [RECOVERY] Could not start {container}: {details}")

    log_recovery_action(ts, service, reason, "start_container", "SUCCESS" if ok else "FAILED", details)
    return ok


def reconnect_network(service, reason):
    ts = datetime.now().isoformat()
    container = get_container_name(service, running_only=False)
    network = get_network_name()

    connect = run_cmd(["docker", "network", "connect", network, container])
    ok = connect.returncode == 0
    details = connect.stdout.strip() if ok else connect.stderr.strip()

    if not ok and "already exists" in details.lower():
        ok = True
        details = "already connected"

    if ok:
        print(f"  [RECOVERY] Network ok for {container} on {network}.")
        restart_time[service] = time.time()
    else:
        print(f"  [RECOVERY] Network reconnect failed for {container}: {details}")

    log_recovery_action(ts, service, reason, "reconnect_network", "SUCCESS" if ok else "FAILED", details)
    return ok


def recover_service(service, failure_type):
    """Use targeted recovery by failure type before fallback restart."""
    if failure_type == "CONTAINER_STOPPED":
        if not start_container(service, failure_type):
            restart_container(service, failure_type)
        return

    if failure_type == "NETWORK_ERROR":
        if not reconnect_network(service, failure_type):
            restart_container(service, failure_type)
        return

    # TIMEOUT / HTTP_ERROR / UNKNOWN_ERROR
    restart_container(service, failure_type)


def classify_connection_error(service):
    if not is_container_running(service):
        return "CONTAINER_STOPPED"
    return "NETWORK_ERROR"


def detect_failure(service, url):
    timestamp = datetime.now().isoformat()
    response_ms = 0.0
    status_code = 0
    success = 0
    failure_type = "NONE"

    try:
        start = time.perf_counter()
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response_ms = (time.perf_counter() - start) * 1000
        status_code = response.status_code
        success = 1 if response.status_code == 200 else 0
        if not success:
            failure_type = "HTTP_ERROR"
    except requests.exceptions.Timeout:
        failure_type = "TIMEOUT"
    except requests.exceptions.ConnectionError:
        failure_type = classify_connection_error(service)
    except Exception as exc:
        failure_type = "UNKNOWN_ERROR"
        print(f"  [ERR] {service} unexpected error: {exc}")

    return timestamp, status_code, success, failure_type, response_ms


def print_health_line(service, failure_type, status_code, response_ms):
    if failure_type == "NONE":
        print(f"  [UP]  {service} ({response_ms:.1f} ms)")
        return
    if failure_type == "HTTP_ERROR":
        print(f"  [ERR] {service} -> HTTP {status_code} ({failures[service]}/{FAILURE_THRESHOLD})")
    elif failure_type == "TIMEOUT":
        print(f"  [ERR] {service} -> TIMEOUT ({failures[service]}/{FAILURE_THRESHOLD})")
    elif failure_type == "CONTAINER_STOPPED":
        print(f"  [ERR] {service} -> CONTAINER STOPPED ({failures[service]}/{FAILURE_THRESHOLD})")
    elif failure_type == "NETWORK_ERROR":
        print(f"  [ERR] {service} -> NETWORK ERROR ({failures[service]}/{FAILURE_THRESHOLD})")
    else:
        print(f"  [ERR] {service} -> UNKNOWN_ERROR ({failures[service]}/{FAILURE_THRESHOLD})")


# -- Startup -----------------------------------------------
print("=" * 56)
print("  Self-Healing Monitor - STARTED")
print(f"  Failure Threshold : {FAILURE_THRESHOLD}")
print(f"  Max Restarts      : {MAX_RESTARTS}")
print(f"  Check Interval    : {CHECK_INTERVAL}s")
print(f"  Restart Grace     : {RESTART_GRACE}s")
print(f"  Request Timeout   : {REQUEST_TIMEOUT}s")
print(f"  Docker Network    : {get_network_name()}")
print()
print("  Detected containers:")
for svc in SERVICES:
    print(f"    {svc} -> {get_container_name(svc, running_only=False)}")
print("=" * 56)


while True:
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{now}] Checking services...")

    for service, url in SERVICES.items():
        if in_grace_period(service):
            continue

        timestamp, status_code, success, failure_type, response_ms = detect_failure(service, url)

        if success == 1:
            failures[service] = 0
            restart_counts[service] = 0
            alerted[service] = False
        else:
            failures[service] += 1

        print_health_line(service, failure_type, status_code, response_ms)
        log_check(timestamp, service, status_code, success, failure_type, response_ms)

        if failures[service] >= FAILURE_THRESHOLD:
            failures[service] = 0

            if restart_counts[service] < MAX_RESTARTS:
                recover_service(service, failure_type)
                restart_counts[service] += 1
            else:
                if not alerted[service]:
                    print(f"\n  [ALERT] {service} - max restarts exceeded! Sending email...")
                    send_email(service, f"Max restarts exceeded - {failure_type}")
                    alerted[service] = True
                else:
                    print(f"  [ALERT] {service} still down - manual intervention required")

    check_count += 1
    if check_count % 10 == 0:
        print("\n  -- Uptime Report --")
        for svc in SERVICES:
            print(f"    {svc}: {calculate_uptime(svc):.1f}%")
        print(f"    Overall: {calculate_uptime():.1f}%")
        print("  -------------------")

    time.sleep(CHECK_INTERVAL)
