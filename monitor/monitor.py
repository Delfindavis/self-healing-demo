import time
import requests
import subprocess

from datetime import datetime
from db import init_db, log_check
from uptime import calculate_uptime

services = {
    "webapp-main": "http://localhost:5000/health",
    "webapp-auth": "http://localhost:5001/health",
    "webapp-payment": "http://localhost:5002/health"
}
INTERVAL = 10  

init_db() 

check_count = 0 

while True:
    try:
        r = requests.get(URL, timeout=5)
        ok = (r.status_code == 200)
        ts = datetime.utcnow().isoformat()

        # Log each health check
        log_check(ts, r.status_code, int(ok))
        print(f"[{ts}] Status: {r.status_code}, OK={ok}")

    except Exception as e:
        ts = datetime.utcnow().isoformat()
        log_check(ts, 0, 0)
        print(f"[{ts}] Error: {e}")

    # Increment total check counter
    check_count += 1

    # ✅ Print uptime every 10 checks
    if check_count % 10 == 0:
        uptime = calculate_uptime()
        print(f"Current uptime: {uptime:.2f}%")

    time.sleep(INTERVAL)



# Services to monitor
services = {
    "webapp-main": "http://localhost:5000/health",
    "webapp-auth": "http://localhost:5001/health",
    "webapp-payment": "http://localhost:5002/health"
}

# Failure counters
failures = {
    "webapp-main": 0,
    "webapp-auth": 0,
    "webapp-payment": 0
}

FAILURE_THRESHOLD = 3
CHECK_INTERVAL = 10  # seconds


def restart_container(container_name):
    print(f"🔄 Restarting container: {container_name}")
    subprocess.run(["docker", "restart", container_name])


while True:
    print("\n🔍 Checking services status...")

    for service, url in services.items():
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ {service} : UP")
                failures[service] = 0
            else:
                raise Exception("Non-200 response")

        except Exception:
            failures[service] += 1
            print(f"❌ {service} : DOWN (failure {failures[service]})")

            if failures[service] >= FAILURE_THRESHOLD:
                restart_container(service)
                failures[service] = 0

    time.sleep(CHECK_INTERVAL)
