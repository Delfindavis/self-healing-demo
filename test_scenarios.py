import argparse
import sqlite3
import subprocess
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "monitor" / "monitor.db"
SERVICES = {
    "webapp-main": "http://localhost:5000",
    "webapp-auth": "http://localhost:5001",
    "webapp-payment": "http://localhost:5002",
}


def run_cmd(command):
    return subprocess.run(command, capture_output=True, text=True)


def get_container_name(service):
    result = run_cmd(["docker", "ps", "-a", "--format", "{{.Names}}"])
    if result.returncode != 0:
        return service
    names = [n.strip() for n in result.stdout.splitlines() if n.strip()]
    for name in names:
        if name == service or name.endswith(f"_{service}_1"):
            return name
    for name in names:
        if service in name:
            return name
    return service


def get_network_name():
    result = run_cmd(["docker", "network", "ls", "--format", "{{.Name}}"])
    if result.returncode != 0:
        return "self-healing-demo_default"
    for name in result.stdout.splitlines():
        n = name.strip().lower()
        if "self-healing-demo" in n:
            return name.strip()
    for name in result.stdout.splitlines():
        n = name.strip().lower()
        if "self-healing" in n:
            return name.strip()
    return "self-healing-demo_default"


def wait_for_health(base_url, timeout_s=90):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/health", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def fetch_recent_counts(window_minutes=5):
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute(
        """
        SELECT failure_type, COUNT(*)
        FROM checks
        WHERE ts >= datetime('now', ?)
        GROUP BY failure_type
        """,
        (f"-{window_minutes} minutes",),
    ).fetchall()
    recovery = c.execute(
        """
        SELECT action, result, COUNT(*)
        FROM recovery_actions
        WHERE ts >= datetime('now', ?)
        GROUP BY action, result
        """,
        (f"-{window_minutes} minutes",),
    ).fetchall()
    conn.close()
    return {"checks": rows, "recovery": recovery}


def scenario_crash():
    print("\n[SCENARIO] Container crash on webapp-main")
    requests.get(f"{SERVICES['webapp-main']}/crash", timeout=1)


def scenario_slow():
    print("\n[SCENARIO] Slow response on webapp-auth")
    try:
        requests.get(f"{SERVICES['webapp-auth']}/slow", timeout=1)
    except Exception:
        pass


def scenario_network():
    print("\n[SCENARIO] Network disconnect on webapp-payment")
    container = get_container_name("webapp-payment")
    network = get_network_name()
    result = run_cmd(["docker", "network", "disconnect", network, container])
    if result.returncode != 0 and "not connected" not in result.stderr.lower():
        raise RuntimeError(f"disconnect failed: {result.stderr.strip()}")


def run():
    parser = argparse.ArgumentParser(description="Run self-healing scenario tests.")
    parser.add_argument("--wait", type=int, default=45, help="Seconds to wait after each trigger.")
    args = parser.parse_args()

    print("Checking baseline health...")
    for name, base in SERVICES.items():
        if not wait_for_health(base, timeout_s=45):
            raise RuntimeError(f"{name} is not healthy before tests. Start docker + monitor first.")
        print(f"  PASS baseline: {name}")

    # Scenario 1: crash
    try:
        scenario_crash()
    except Exception:
        # /crash forcibly exits process, request can fail on client side; this is acceptable.
        pass
    time.sleep(args.wait)
    print("  PASS trigger: crash sent")

    # Scenario 2: slow timeout
    scenario_slow()
    time.sleep(args.wait)
    print("  PASS trigger: slow sent")

    # Scenario 3: network disconnect
    scenario_network()
    time.sleep(args.wait)
    print("  PASS trigger: network disconnect sent")

    print("\nVerifying services recover to healthy...")
    for name, base in SERVICES.items():
        ok = wait_for_health(base, timeout_s=120)
        print(f"  {'PASS' if ok else 'FAIL'} recovery: {name}")

    print("\nRecent DB evidence (last 5 minutes):")
    summary = fetch_recent_counts(window_minutes=5)
    print("  checks by failure_type:", summary.get("checks", []))
    print("  recovery actions:", summary.get("recovery", []))
    print("\nDone. If monitor was running, you should now have graph-ready incident data in DB.")


if __name__ == "__main__":
    run()
