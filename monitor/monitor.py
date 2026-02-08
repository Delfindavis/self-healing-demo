import time
import requests
import subprocess

URL = "http://localhost:5000/health"
failures = 0

while True:
    try:
        r = requests.get(URL, timeout=3)
        if r.status_code == 200:
            print("App is UP")
            failures = 0
        else:
            failures += 1
    except:
        print("App is DOWN")
        failures += 1

    print("Failure count:", failures)

    if failures >= 3:
        print("Restarting container...")
        subprocess.run(["docker", "restart", "webapp"])
        failures = 0

    time.sleep(10)
