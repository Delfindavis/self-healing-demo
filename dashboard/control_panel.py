from flask import Flask, render_template_string, jsonify
import sqlite3
import requests
import subprocess
from pathlib import Path

app = Flask(__name__)
DB = str(Path(__file__).resolve().parent.parent / "monitor" / "monitor.db")

SERVICES = {
    "webapp-main":    5000,
    "webapp-auth":    5001,
    "webapp-payment": 5002
}


def get_container_name(service):
    """Find actual Docker container name for a service."""
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    for name in result.stdout.strip().split("\n"):
        if service in name:
            return name.strip()
    return service


def get_network_name():
    """Auto-detect docker-compose network name."""
    result = subprocess.run(
        ["docker", "network", "ls", "--format", "{{.Name}}"],
        capture_output=True, text=True
    )
    for name in result.stdout.strip().split("\n"):
        if "self-healing" in name.lower() or "healing" in name.lower():
            return name.strip()
    return "self-healing-demo_default"


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Control Panel</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#060a0f; --panel:#0b1018; --border:#1a2535;
    --green:#00ff88; --red:#ff3b5c; --yellow:#ffcc00;
    --blue:#38bdf8; --muted:#4a5568; --text:#c9d1d9;
  }
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;
    padding:28px;min-height:100vh;
    background-image:radial-gradient(ellipse at 50% 0%,#0a1628 0%,transparent 70%)}

  header{text-align:center;margin-bottom:24px}
  h1{font-size:1.4rem;font-weight:700;color:#fff;letter-spacing:2px;text-transform:uppercase}
  .tagline{font-size:0.7rem;color:var(--muted);margin-top:6px;letter-spacing:3px}

  .topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
  .info{font-size:0.65rem;color:var(--muted)}
  .info span{color:var(--blue)}
  .link-btn{padding:8px 20px;border-radius:6px;font-size:0.72rem;font-family:'JetBrains Mono',monospace;
    text-decoration:none;border:1px solid #38bdf855;color:var(--blue);background:#38bdf811}

  .guide{background:var(--panel);border:1px solid #ffcc0022;border-radius:10px;
    padding:14px 18px;margin-bottom:22px}
  .guide-title{font-size:0.65rem;color:var(--yellow);letter-spacing:2px;
    text-transform:uppercase;margin-bottom:10px}
  .guide-row{font-size:0.67rem;display:flex;gap:16px;padding:4px 0;
    border-bottom:1px solid #0e1620}
  .guide-row:last-child{border-bottom:none}
  .guide-key{color:var(--text);min-width:180px}
  .guide-val{color:var(--muted)}

  .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-bottom:22px}
  @media(max-width:900px){.grid{grid-template-columns:1fr}}

  .card{background:var(--panel);border:1px solid var(--border);border-radius:12px;overflow:hidden}
  .card-header{padding:14px 18px;border-bottom:1px solid var(--border);
    display:flex;align-items:center;justify-content:space-between}
  .svc-name{font-size:0.85rem;font-weight:700;color:#fff}
  .svc-badge{font-size:0.65rem;padding:3px 10px;border-radius:20px;font-weight:600}
  .badge-up  {background:#00ff8818;color:var(--green);border:1px solid #00ff8840}
  .badge-down{background:#ff3b5c18;color:var(--red);  border:1px solid #ff3b5c40}
  .card-body{padding:14px 18px}
  .info-row{display:flex;justify-content:space-between;font-size:0.68rem;
    color:var(--muted);margin-bottom:6px}
  .info-val{color:var(--text)}
  .info-err{color:var(--red)}

  .btn-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:14px}
  .btn{padding:9px 6px;border-radius:7px;font-size:0.65rem;
    font-family:'JetBrains Mono',monospace;cursor:pointer;border:none;
    font-weight:700;letter-spacing:0.5px;transition:all 0.15s;text-align:center}
  .btn:hover{opacity:0.8;transform:translateY(-1px)}
  .btn:active{transform:scale(0.97)}
  .btn-red   {background:#ff3b5c22;color:var(--red);   border:1px solid #ff3b5c55}
  .btn-yellow{background:#ffcc0022;color:var(--yellow);border:1px solid #ffcc0055}
  .btn-blue  {background:#38bdf822;color:var(--blue);  border:1px solid #38bdf855}
  .btn-green {background:#00ff8822;color:var(--green); border:1px solid #00ff8855}
  .btn-full  {grid-column:span 2}
  .btn:disabled{opacity:0.3;cursor:not-allowed;transform:none}

  .toast{position:fixed;bottom:24px;right:24px;background:#0b1018;
    border:1px solid var(--border);border-radius:8px;padding:12px 18px;
    font-size:0.72rem;max-width:400px;display:none;z-index:999;
    box-shadow:0 8px 32px #00000088;line-height:1.6}
  .toast.show{display:block;animation:fadeIn 0.3s ease}
  .toast.ok  {color:var(--green); border-color:#00ff8833}
  .toast.err {color:var(--red);   border-color:#ff3b5c33}
  .toast.info{color:var(--yellow);border-color:#ffcc0033}
  @keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

  .log-panel{background:var(--panel);border:1px solid var(--border);
    border-radius:12px;padding:18px}
  .log-title{font-size:0.65rem;color:var(--blue);letter-spacing:2px;
    text-transform:uppercase;margin-bottom:12px}
  .log-entry{font-size:0.68rem;padding:6px 0;border-bottom:1px solid #0e1620;
    display:flex;gap:14px;align-items:center}
  .log-entry:last-child{border-bottom:none}
  .log-time{color:var(--blue);min-width:80px;flex-shrink:0}
  .log-svc{color:#fff;min-width:130px;flex-shrink:0}
  .log-msg{color:var(--yellow)}
</style>
</head>
<body>

<header>
  <h1>⚡ Test Control Panel</h1>
  <div class="tagline">FAILURE SIMULATION — SELF-HEALING DEMO</div>
</header>

<div class="topbar">
  <div class="info">
    Network: <span id="net-name">...</span> &nbsp;|&nbsp;
    Containers: <span id="containers">...</span>
  </div>
  <a class="link-btn" href="http://localhost:8081" target="_blank">→ Analytics Dashboard</a>
</div>

<div class="guide">
  <div class="guide-title">📋 Test Cases</div>
  <div class="guide-row"><span class="guide-key">💥 CRASH</span><span class="guide-val">Kills container → CONTAINER_STOPPED → monitor auto-restarts (up to 3x)</span></div>
  <div class="guide-row"><span class="guide-key">⏱ SLOW</span><span class="guide-val">Blocks service 10s → TIMEOUT → monitor restarts after 3 timeouts</span></div>
  <div class="guide-row"><span class="guide-key">🔀 TOGGLE HEALTH</span><span class="guide-val">HTTP 500 response → HTTP_ERROR → monitor restarts after 3 fails</span></div>
  <div class="guide-row"><span class="guide-key">✅ RESTORE</span><span class="guide-val">Checks current state and resets to healthy HTTP 200</span></div>
  <div class="guide-row"><span class="guide-key">🌐 NETWORK ERROR</span><span class="guide-val">Disconnects container from Docker network → NETWORK_ERROR</span></div>
  <div class="guide-row"><span class="guide-key">🔓 RECONNECT</span><span class="guide-val">Reconnects container to Docker network → service recovers</span></div>
</div>

<div class="grid" id="cards"></div>

<div class="log-panel">
  <div class="log-title">Action Log</div>
  <div id="log"><div style="color:var(--muted);font-size:0.7rem">No actions yet</div></div>
</div>

<div class="toast" id="toast"></div>

<script>
const services = ["webapp-main","webapp-auth","webapp-payment"];
let statusCache = {};
let actionLog   = [];

// Load docker info
fetch("/api/info").then(r=>r.json()).then(d=>{
  document.getElementById("net-name").textContent    = d.network;
  document.getElementById("containers").textContent  = Object.values(d.containers).join(", ");
});

function showToast(msg, type="info") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className   = `toast show ${type}`;
  clearTimeout(t._t);
  t._t = setTimeout(() => t.classList.remove("show"), 5000);
}

function addLog(svc, msg) {
  const now = new Date().toTimeString().slice(0,8);
  actionLog.unshift({time:now, svc, msg});
  if(actionLog.length > 12) actionLog.pop();
  document.getElementById("log").innerHTML = actionLog.map(e =>
    `<div class="log-entry">
      <span class="log-time">${e.time}</span>
      <span class="log-svc">${e.svc}</span>
      <span class="log-msg">${e.msg}</span>
    </div>`).join("");
}

async function trigger(service, action, label) {
  document.querySelectorAll('.btn').forEach(b => b.disabled = true);
  try {
    const res  = await fetch(`/control/${service}/${action}`);
    const data = await res.json();
    addLog(service, label);
    const isErr = data.message.toLowerCase().includes("fail") ||
                  data.message.toLowerCase().includes("error") ||
                  data.message.toLowerCase().includes("cannot");
    showToast(data.message, isErr ? "err" : "ok");
  } catch(e) {
    showToast(`Request error: ${e.message}`, "err");
  } finally {
    setTimeout(()=>document.querySelectorAll('.btn').forEach(b=>b.disabled=false), 1500);
  }
}

function renderCards() {
  document.getElementById("cards").innerHTML = services.map(svc => {
    const s    = statusCache[svc] || {};
    const isUp = s.ok == 1;
    const ftc  = s.failure_type && s.failure_type !== "NONE" ? "info-err" : "info-val";
    return `
    <div class="card">
      <div class="card-header">
        <span class="svc-name">${svc}</span>
        <span class="svc-badge ${isUp?'badge-up':'badge-down'}">${isUp?'● UP':'● DOWN'}</span>
      </div>
      <div class="card-body">
        <div class="info-row"><span>HTTP STATUS</span>
          <span class="info-val">${s.status||'--'}</span></div>
        <div class="info-row"><span>FAILURE TYPE</span>
          <span class="${ftc}">${s.failure_type||'--'}</span></div>
        <div class="info-row"><span>LAST CHECK</span>
          <span class="info-val">${s.ts?s.ts.slice(11,19):'--'}</span></div>
        <div class="btn-grid">
          <button class="btn btn-red"
            onclick="trigger('${svc}','crash','💥 Crash')">💥 CRASH</button>
          <button class="btn btn-yellow"
            onclick="trigger('${svc}','slow','⏱ Slow')">⏱ SLOW</button>
          <button class="btn btn-blue"
            onclick="trigger('${svc}','toggle','🔀 Toggle Health')">🔀 TOGGLE</button>
          <button class="btn btn-green"
            onclick="trigger('${svc}','restore','✅ Restore')">✅ RESTORE</button>
          <button class="btn btn-red btn-full"
            onclick="trigger('${svc}','network','🌐 Network Error')">🌐 NETWORK ERROR</button>
          <button class="btn btn-green btn-full"
            onclick="trigger('${svc}','reconnect','🔓 Reconnect')">🔓 RECONNECT NETWORK</button>
        </div>
      </div>
    </div>`;
  }).join("");
}

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    statusCache = await res.json();
    renderCards();
  } catch(e) {}
}

renderCards();
loadStatus();
setInterval(loadStatus, 5000);
</script>
</body>
</html>
"""


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/info")
def api_info():
    containers = {svc: get_container_name(svc) for svc in SERVICES}
    return jsonify({"network": get_network_name(), "containers": containers})


@app.route("/api/status")
def api_status():
    try:
        conn = get_db()
        c    = conn.cursor()
        c.execute("SELECT service, status, ok, failure_type, ts FROM checks ORDER BY ts DESC")
        rows = c.fetchall()
        conn.close()
        result = {}
        for r in rows:
            if r["service"] not in result:
                result[r["service"]] = dict(r)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/control/<service>/<action>")
def control(service, action):
    port      = SERVICES.get(service)
    container = get_container_name(service)
    network   = get_network_name()
    msg       = "done"

    try:

        # ── CRASH ───────────────────────────────────────────
        if action == "crash":
            try:
                requests.get(f"http://localhost:{port}/crash", timeout=2)
            except:
                pass
            msg = f"Crash triggered ({container}) — monitor detects CONTAINER_STOPPED in ~10s"

        # ── SLOW ────────────────────────────────────────────
        elif action == "slow":
            # Fire request with tiny timeout — container blocks for 10s
            # monitor's /health check will also timeout
            try:
                requests.get(f"http://localhost:{port}/slow", timeout=0.5)
            except:
                pass
            msg = f"Slow response triggered — {container} blocked 10s — monitor detects TIMEOUT"

        # ── TOGGLE HEALTH ────────────────────────────────────
        elif action == "toggle":
            r    = requests.get(f"http://localhost:{port}/toggle-health", timeout=3)
            data = r.json()
            state = data.get("toggled_to", "unknown")
            msg   = f"Toggled to {state.upper()} — monitor will detect {'HTTP_ERROR' if state=='unhealthy' else 'UP'}"

        # ── RESTORE HEALTH ───────────────────────────────────
        elif action == "restore":
            try:
                health = requests.get(f"http://localhost:{port}/health", timeout=3)
                if health.status_code != 200:
                    # Currently unhealthy — toggle back to healthy
                    requests.get(f"http://localhost:{port}/toggle-health", timeout=3)
                    msg = f"{service} restored to HEALTHY — monitor will see HTTP 200 on next check"
                else:
                    msg = f"{service} is already HEALTHY (HTTP 200) — no action needed"
            except requests.exceptions.ConnectionError:
                msg = f"Cannot reach {service} — container may be stopped or crashed. Monitor will auto-restart it."
            except requests.exceptions.Timeout:
                msg = f"{service} is still slow/blocked — wait for it to finish or it will timeout and restart"

        # ── NETWORK ERROR ─────────────────────────────────────
        elif action == "network":
            result = subprocess.run(
                ["docker", "network", "disconnect", network, container],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                msg = f"Disconnected {container} from {network} — monitor detects NETWORK_ERROR in ~10s"
            else:
                err = result.stderr.strip()
                if "not connected" in err.lower():
                    msg = f"{container} is not connected to {network} (already disconnected?)"
                else:
                    msg = f"Disconnect failed: {err}"

        # ── RECONNECT NETWORK ─────────────────────────────────
        elif action == "reconnect":
            result = subprocess.run(
                ["docker", "network", "connect", network, container],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                msg = f"Reconnected {container} to {network} — service recovering in ~10s"
            else:
                err = result.stderr.strip()
                if "already exists" in err.lower():
                    msg = f"{container} is already connected to the network"
                else:
                    msg = f"Reconnect failed: {err}"

    except requests.exceptions.ConnectionError:
        msg = f"{service} is unreachable — container may be crashed"
    except Exception as e:
        msg = f"Unexpected error: {str(e)}"

    return jsonify({"message": msg})


if __name__ == "__main__":
    app.run(port=7000, debug=True)