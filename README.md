# Self-Healing Demo

This demo runs three Flask microservices, a monitor that auto-restarts failing services, and an analytics dashboard for developer visibility.

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

4. Start analytics dashboard (optional):

   ```bash
   python dashboard/Analytical_Dashboard.py
   ```

## Test

Run lightweight endpoint tests:

```bash
python -m pytest -q
```

## Failure Scenario Testing (Automated)

Start monitor in one terminal:

```bash
python monitor/monitor.py
```

Then run the one-command scenario runner:

```bash
python test_scenarios.py
```

What the automated runner does:

- validates baseline health for all services
- triggers crash, slow/timeout, and network-disconnect scenarios
- waits for recovery and checks services are healthy again
- prints DB evidence from `checks` and `recovery_actions`

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

Optional wait tuning between scenarios:

```bash
python test_scenarios.py --wait 60
```

## URLs

- Services:
  - `http://localhost:5000`
  - `http://localhost:5001`
  - `http://localhost:5002`
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
