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
