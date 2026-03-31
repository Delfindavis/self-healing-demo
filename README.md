# Self-Healing Demo

This demo runs three Flask microservices, a monitor that auto-restarts failing services, and two dashboards.

## Run

1. Start services with Docker:

   ```bash
   docker compose up --build
   ```

2. In another terminal, install local Python deps:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Start monitor:

   ```bash
   python monitor/monitor.py
   ```

4. Start dashboards (optional):

   ```bash
   python dashboard/control_panel.py
   python dashboard/Analytical_Dashboard.py
   ```

## Test

Run lightweight endpoint tests:

```bash
python -m pytest -q
```

## Failure Scenario Testing

Start monitor in one terminal:

```bash
python monitor/monitor.py
```

Use these scenario triggers from another terminal:

1. Container crash

```bash
curl http://localhost:5000/crash
```

- Expected monitor behavior: logs `CONTAINER_STOPPED`, then runs `start_container` (or restart fallback).

2. Slow network / timeout simulation

```bash
curl http://localhost:5001/slow
```

- Expected monitor behavior: logs `TIMEOUT`, then restarts container after threshold is reached.

3. Network disconnect simulation

```bash
docker network disconnect self-healing-demo_default self-healing-demo-webapp-payment-1
```

- Expected monitor behavior: logs `NETWORK_ERROR`, then runs `reconnect_network` recovery.

Optional reconnect command (manual):

```bash
docker network connect self-healing-demo_default self-healing-demo-webapp-payment-1
```

## DB Data For Developer Graphs

Monitor stores graph-ready data in:

- `checks`: per-check health status + failure type + latency (`response_ms`)
- `restarts`: restart timeline
- `recovery_actions`: action attempted (`start_container`, `reconnect_network`, `restart_container`) and result
- `email_logs`: alert delivery log

Quick check with SQLite:

```bash
python -c "import sqlite3; c=sqlite3.connect('monitor/monitor.db').cursor(); print(c.execute('select service,failure_type,count(*) from checks group by service,failure_type').fetchall())"
```

### One-command scenario runner

If Docker services and monitor are already running, run:

```bash
python test_scenarios.py
```

Optional wait tuning between scenarios:

```bash
python test_scenarios.py --wait 60
```

## URLs

- Services:
  - `http://localhost:5000`
  - `http://localhost:5001`
  - `http://localhost:5002`
- Control panel: `http://localhost:7000`
- Analytics dashboard: `http://localhost:8081`

## Notes

- Monitor database is stored at `monitor/monitor.db`.
- Email alerts require env vars:
  - `SENDER_EMAIL`
  - `APP_PASSWORD`
- On Windows PowerShell, set email vars with:

  ```powershell
  $env:SENDER_EMAIL="you@example.com"
  $env:APP_PASSWORD="your-app-password"
  ```
