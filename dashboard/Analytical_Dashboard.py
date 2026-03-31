from flask import Flask, render_template_string, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB = str(Path(__file__).resolve().parent.parent / "monitor" / "monitor.db")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HEALFUX — Analytics</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;600&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
:root{
  --bg:#050810;--bg2:#07090f;--panel:#0b1220;
  --border:#152035;--green:#00e676;--red:#ff1744;--yellow:#ffd740;
  --blue:#40c4ff;--purple:#e040fb;--text:#cdd6f4;--muted:#45546a;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;
  background-image:radial-gradient(ellipse at 0% 0%,#071428 0%,transparent 50%),
    radial-gradient(ellipse at 100% 100%,#07140a 0%,transparent 50%)}

.sidebar{position:fixed;left:0;top:0;bottom:0;width:220px;background:var(--bg2);
  border-right:1px solid var(--border);padding:28px 0;z-index:100;display:flex;flex-direction:column}
.logo{padding:0 24px 28px;border-bottom:1px solid var(--border)}
.logo-name{font-size:1.1rem;font-weight:800;color:#fff;letter-spacing:1px}
.logo-sub{font-size:0.62rem;color:var(--muted);font-family:'JetBrains Mono',monospace;letter-spacing:2px;margin-top:3px}
.nav{padding:20px 0;flex:1}
.nav-item{display:flex;align-items:center;gap:10px;padding:11px 24px;font-size:0.78rem;
  color:var(--muted);cursor:pointer;transition:all 0.2s;letter-spacing:0.5px;text-decoration:none}
.nav-item:hover,.nav-item.active{color:#fff;background:linear-gradient(90deg,#ffffff08 0%,transparent 100%)}
.nav-item.active{border-left:2px solid var(--blue);color:var(--blue)}
.nav-dot{width:6px;height:6px;border-radius:50%}
.sidebar-bottom{padding:16px 24px;border-top:1px solid var(--border)}
.live-ind{display:flex;align-items:center;gap:8px;font-size:0.65rem;color:var(--green);font-family:'JetBrains Mono',monospace}
.pulse{width:7px;height:7px;border-radius:50%;background:var(--green);animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 0 0 #00e67644}50%{opacity:0.5;box-shadow:0 0 0 4px #00e67600}}

.main{margin-left:220px;padding:32px 36px;min-height:100vh}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:36px}
.page-title{font-size:1.6rem;font-weight:800;color:#fff;letter-spacing:-0.5px}
.page-sub{font-size:0.72rem;color:var(--muted);font-family:'JetBrains Mono',monospace;margin-top:4px}
.top-actions{display:flex;gap:10px}
.btn-outline{padding:8px 18px;border-radius:7px;font-size:0.72rem;font-family:'JetBrains Mono',monospace;
  background:transparent;border:1px solid var(--border);color:var(--text);cursor:pointer;transition:all 0.2s}
.btn-outline:hover{border-color:var(--blue);color:var(--blue)}
.btn-primary{padding:8px 18px;border-radius:7px;font-size:0.72rem;font-family:'JetBrains Mono',monospace;
  background:var(--blue);border:none;color:#000;cursor:pointer;font-weight:600;transition:opacity 0.2s}
.btn-primary:hover{opacity:0.85}

.stats-row{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:28px}
.stat{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:20px 22px;position:relative;overflow:hidden}
.stat::after{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.stat.s-green::after{background:linear-gradient(90deg,var(--green),transparent)}
.stat.s-red::after{background:linear-gradient(90deg,var(--red),transparent)}
.stat.s-blue::after{background:linear-gradient(90deg,var(--blue),transparent)}
.stat.s-yellow::after{background:linear-gradient(90deg,var(--yellow),transparent)}
.stat.s-purple::after{background:linear-gradient(90deg,var(--purple),transparent)}
.stat-icon{font-size:1.3rem;margin-bottom:10px}
.stat-label{font-size:0.65rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:6px;font-family:'JetBrains Mono',monospace}
.stat-value{font-size:1.9rem;font-weight:800;color:#fff;line-height:1}
.stat-change{font-size:0.65rem;color:var(--muted);margin-top:6px;font-family:'JetBrains Mono',monospace}

.service-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:28px}
.svc-card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:20px}
.svc-card.up{border-color:#00e67622}.svc-card.down{border-color:#ff174422}
.svc-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.svc-name{font-size:0.85rem;font-weight:700;color:#fff}
.svc-badge{font-size:0.65rem;padding:3px 10px;border-radius:20px;font-family:'JetBrains Mono',monospace;font-weight:600}
.badge-up{background:#00e67615;color:var(--green);border:1px solid #00e67635}
.badge-down{background:#ff174415;color:var(--red);border:1px solid #ff174435}
.svc-uptime{font-size:2rem;font-weight:800;margin-bottom:8px}
.uptime-bar{height:4px;background:var(--border);border-radius:2px;margin-bottom:10px}
.uptime-fill{height:100%;border-radius:2px}
.svc-meta{display:flex;justify-content:space-between;font-size:0.65rem;color:var(--muted);font-family:'JetBrains Mono',monospace}
.restart-limit{font-size:0.65rem;margin-top:8px;font-family:'JetBrains Mono',monospace;
  padding:4px 8px;border-radius:4px;background:#ffd74015;color:var(--yellow);border:1px solid #ffd74030;display:inline-block}

.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:28px}
.chart-full{grid-column:span 2}
.chart-card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:22px}
.chart-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.chart-title{font-size:0.78rem;font-weight:700;color:#fff;letter-spacing:0.5px}
.chart-sub{font-size:0.62rem;color:var(--muted);font-family:'JetBrains Mono',monospace;margin-top:3px}

.timeline{display:flex;flex-direction:column}
.tl-item{display:flex;gap:16px;padding:12px 0;border-bottom:1px solid #0d1825;align-items:flex-start}
.tl-item:last-child{border-bottom:none}
.tl-dot{width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0;background:var(--yellow)}
.tl-content{flex:1}
.tl-title{font-size:0.78rem;color:#fff;margin-bottom:3px}
.tl-meta{font-size:0.65rem;color:var(--muted);font-family:'JetBrains Mono',monospace}
.tl-badge{font-size:0.62rem;padding:2px 8px;border-radius:4px;
  background:#ffd74015;color:var(--yellow);border:1px solid #ffd74030;margin-left:8px}
.tl-time{font-size:0.65rem;color:var(--muted);font-family:'JetBrains Mono',monospace;flex-shrink:0}

.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th{font-size:0.62rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);
  font-family:'JetBrains Mono',monospace;padding:10px 16px;text-align:left;
  border-bottom:1px solid var(--border);font-weight:400}
td{padding:10px 16px;font-size:0.75rem;border-bottom:1px solid #0a1020;font-family:'JetBrains Mono',monospace}
tr:last-child td{border-bottom:none}tr:hover td{background:#0d1828}
.pill{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.65rem;font-weight:600}
.pill-up  {background:#00e67615;color:var(--green);border:1px solid #00e67630}
.pill-down{background:#ff174415;color:var(--red);  border:1px solid #ff174430}
.pill-warn{background:#ffd74015;color:var(--yellow);border:1px solid #ffd74030}
.pill-none{background:#45546a15;color:var(--muted); border:1px solid #45546a30}
.pill-sent{background:#00e67615;color:var(--green);border:1px solid #00e67630}
.pill-fail{background:#ff174415;color:var(--red);  border:1px solid #ff174430}
.svc-tag{color:var(--blue)}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="logo">
    <div class="logo-name"> HEALFIX</div>
    <div class="logo-sub">MONITORING ANALYTICS</div>
  </div>
  <nav class="nav">
    <a class="nav-item active" href="#"><div class="nav-dot" style="background:var(--blue)"></div>Overview</a>
    <a class="nav-item" href="#"><div class="nav-dot" style="background:var(--green)"></div>Services</a>
    <a class="nav-item" href="#"><div class="nav-dot" style="background:var(--yellow)"></div>Incidents</a>
    <a class="nav-item" href="#"><div class="nav-dot" style="background:var(--purple)"></div>Email Alerts</a>
  </nav>
  <div class="sidebar-bottom">
    <div class="live-ind"><div class="pulse"></div>LIVE — AUTO REFRESH 10s</div>
  </div>
</aside>

<main class="main">

  <div class="topbar">
    <div>
      <div class="page-title">System Overview</div>
      <div class="page-sub" id="last-updated">Loading...</div>
    </div>
    <div class="top-actions">
      <a href="http://localhost:7000" target="_blank">
        <button class="btn-outline">⚙ Control Panel</button>
      </a>
      <button class="btn-primary" onclick="loadAll()">↻ Refresh</button>
    </div>
  </div>

  <div class="stats-row">
    <div class="stat s-blue"><div class="stat-icon">📊</div><div class="stat-label">Total Checks</div><div class="stat-value" id="s-total">--</div><div class="stat-change">all time</div></div>
    <div class="stat s-green"><div class="stat-icon">✅</div><div class="stat-label">Successful</div><div class="stat-value" id="s-success">--</div><div class="stat-change">ok responses</div></div>
    <div class="stat s-red"><div class="stat-icon">❌</div><div class="stat-label">Failures</div><div class="stat-value" id="s-fail">--</div><div class="stat-change">detected</div></div>
    <div class="stat s-yellow"><div class="stat-icon">🔄</div><div class="stat-label">Restarts</div><div class="stat-value" id="s-restarts">--</div><div class="stat-change">auto-healed</div></div>
    <div class="stat s-purple"><div class="stat-icon">📈</div><div class="stat-label">Uptime</div><div class="stat-value" id="s-uptime">--</div><div class="stat-change">overall</div></div>
  </div>

  <div class="service-row" id="svc-cards"></div>

  <div class="charts-grid">
    <div class="chart-card chart-full">
      <div class="chart-head"><div><div class="chart-title">Uptime Trend — Last 60 Checks Per Service</div><div class="chart-sub">rolling success rate</div></div></div>
      <canvas id="uptimeChart" height="90"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-head"><div><div class="chart-title">Failure Type Breakdown</div><div class="chart-sub">distribution of all failures</div></div></div>
      <canvas id="failureChart" height="220"></canvas>
    </div>
    <div class="chart-card">
      <div class="chart-head"><div><div class="chart-title">Checks Per Service</div><div class="chart-sub">success vs failure</div></div></div>
      <canvas id="checksChart" height="220"></canvas>
    </div>
  </div>

  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-head"><div><div class="chart-title">Restart Timeline</div><div class="chart-sub">auto-healing events</div></div></div>
      <div class="timeline" id="restart-timeline"></div>
    </div>
    <div class="chart-card">
      <div class="chart-head"><div><div class="chart-title">Recent Health Checks</div><div class="chart-sub">last 15 events</div></div></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Time</th><th>Service</th><th>Status</th><th>Type</th></tr></thead>
          <tbody id="checks-table"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="chart-card chart-full">
      <div class="chart-head">
        <div><div class="chart-title">📧 Email Alert Log</div><div class="chart-sub">notifications sent to developers when restart limit exceeded</div></div>
        <div id="email-count" style="font-size:0.7rem;color:var(--muted);font-family:'JetBrains Mono',monospace"></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Time</th><th>Service</th><th>Reason</th><th>Recipient</th><th>Status</th></tr></thead>
          <tbody id="email-table"></tbody>
        </table>
      </div>
    </div>
  </div>

</main>

<script>
let uptimeChart, failureChart, checksChart;
const COLORS = {
  'webapp-main':    '#40c4ff',
  'webapp-auth':    '#00e676',
  'webapp-payment': '#e040fb',
};

async function loadAll() {
  try {
    const res = await fetch("/api/analytics");
    const d = await res.json();
    if(d.error){ console.error(d.error); return; }

    document.getElementById("last-updated").textContent = "Last updated: " + new Date().toLocaleTimeString();
    document.getElementById("s-total").textContent    = d.total;
    document.getElementById("s-success").textContent  = d.success;
    document.getElementById("s-fail").textContent     = d.fail;
    document.getElementById("s-restarts").textContent = d.restarts;
    document.getElementById("s-uptime").textContent   = d.uptime + "%";

    document.getElementById("svc-cards").innerHTML = d.services.map(s => {
      const color = s.uptime >= 90 ? 'var(--green)' : s.uptime >= 60 ? 'var(--yellow)' : 'var(--red)';
      const restartColor = s.restarts >= 3 ? 'var(--red)' : s.restarts >= 1 ? 'var(--yellow)' : 'var(--green)';
      return `
      <div class="svc-card ${s.is_up?'up':'down'}">
        <div class="svc-top">
          <span class="svc-name">${s.name}</span>
          <span class="svc-badge ${s.is_up?'badge-up':'badge-down'}">${s.is_up?'● HEALTHY':'● DOWN'}</span>
        </div>
        <div class="svc-uptime" style="color:${color}">${s.uptime}%</div>
        <div class="uptime-bar"><div class="uptime-fill" style="width:${s.uptime}%;background:${color}"></div></div>
        <div class="svc-meta">
          <span>${s.total} checks</span>
          <span>last: ${s.last_check}</span>
        </div>
        <div class="restart-limit" style="color:${restartColor};border-color:${restartColor}33;background:${restartColor}11">
          Restarts: ${s.restarts} / 3 max
        </div>
      </div>`;
    }).join("");

    if(uptimeChart) uptimeChart.destroy();
    uptimeChart = new Chart(document.getElementById("uptimeChart"), {
      type:"line",
      data:{
        labels: d.trend.labels,
        datasets: d.services.map(s => ({
          label: s.name, data: d.trend[s.name]||[],
          borderColor: COLORS[s.name]||'#fff',
          backgroundColor: (COLORS[s.name]||'#fff')+'15',
          borderWidth:2, pointRadius:0, tension:0.4, fill:true
        }))
      },
      options:{responsive:true,
        plugins:{legend:{labels:{color:'#cdd6f4',font:{family:'JetBrains Mono',size:11}}}},
        scales:{
          x:{ticks:{color:'#45546a',font:{family:'JetBrains Mono',size:10},maxTicksLimit:8},grid:{color:'#0d1828'}},
          y:{min:0,max:100,ticks:{color:'#45546a',font:{family:'JetBrains Mono',size:10},callback:v=>v+'%'},grid:{color:'#0d1828'}}
        }
      }
    });

    if(failureChart) failureChart.destroy();
    failureChart = new Chart(document.getElementById("failureChart"), {
      type:"doughnut",
      data:{
        labels: d.failure_types.map(f=>f.type),
        datasets:[{data:d.failure_types.map(f=>f.count),
          backgroundColor:['#00e67633','#ff174433','#ffd74033','#40c4ff33','#e040fb33'],
          borderColor:['#00e676','#ff1744','#ffd740','#40c4ff','#e040fb'],borderWidth:2}]
      },
      options:{responsive:true,cutout:'65%',
        plugins:{legend:{position:'bottom',labels:{color:'#cdd6f4',font:{family:'JetBrains Mono',size:11},padding:16}}}}
    });

    if(checksChart) checksChart.destroy();
    checksChart = new Chart(document.getElementById("checksChart"), {
      type:"bar",
      data:{
        labels: d.services.map(s=>s.name),
        datasets:[
          {label:'Successful',data:d.services.map(s=>s.success),backgroundColor:'#00e67633',borderColor:'#00e676',borderWidth:2},
          {label:'Failed',    data:d.services.map(s=>s.failed), backgroundColor:'#ff174433',borderColor:'#ff1744',borderWidth:2}
        ]
      },
      options:{responsive:true,
        plugins:{legend:{labels:{color:'#cdd6f4',font:{family:'JetBrains Mono',size:11}}}},
        scales:{
          x:{ticks:{color:'#45546a',font:{family:'JetBrains Mono',size:10}},grid:{color:'#0d1828'}},
          y:{ticks:{color:'#45546a',font:{family:'JetBrains Mono',size:10}},grid:{color:'#0d1828'}}
        }
      }
    });

    document.getElementById("restart-timeline").innerHTML = d.recent_restarts.length
      ? d.recent_restarts.map(r=>`
        <div class="tl-item">
          <div class="tl-dot"></div>
          <div class="tl-content">
            <div class="tl-title">${r.service} restarted <span class="tl-badge">${r.reason}</span></div>
            <div class="tl-meta">Auto-healed by monitor</div>
          </div>
          <div class="tl-time">${r.ts.slice(11,19)}</div>
        </div>`).join("")
      : '<div style="color:var(--muted);font-size:0.75rem;padding:16px 0">No restarts recorded yet</div>';

    document.getElementById("checks-table").innerHTML = d.recent_checks.map(c=>`
      <tr>
        <td>${c.ts.slice(11,19)}</td>
        <td class="svc-tag">${c.service}</td>
        <td>${c.ok==1?'<span class="pill pill-up">UP</span>':'<span class="pill pill-down">DOWN</span>'}</td>
        <td><span class="pill ${c.failure_type=='NONE'?'pill-none':'pill-warn'}">${c.failure_type}</span></td>
      </tr>`).join("");

    document.getElementById("email-count").textContent = d.email_total + " alerts sent";
    document.getElementById("email-table").innerHTML = d.email_logs.length
      ? d.email_logs.map(e=>`
        <tr>
          <td>${e.ts.slice(11,19)}</td>
          <td class="svc-tag">${e.service}</td>
          <td><span class="pill pill-warn">${e.reason}</span></td>
          <td style="color:var(--muted)">${e.recipient}</td>
          <td><span class="pill ${e.status==='SENT'?'pill-sent':'pill-fail'}">${e.status}</span></td>
        </tr>`).join("")
      : '<tr><td colspan="5" style="color:var(--muted);text-align:center;padding:20px">No emails sent yet — trigger failures 3+ times to exceed restart limit</td></tr>';

  } catch(err) {
    console.error("Load error:", err);
  }
}

loadAll();
setInterval(loadAll, 10000);
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


@app.route("/api/analytics")
def analytics():
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM checks");             total    = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM checks WHERE ok=1");  success  = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM restarts");           restarts = c.fetchone()[0]
        fail   = total - success
        uptime = round(success / total * 100, 1) if total > 0 else 0.0

        services_list = ["webapp-main", "webapp-auth", "webapp-payment"]
        services = []
        for svc in services_list:
            c.execute("SELECT COUNT(*) FROM checks WHERE service=?", (svc,));           t = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM checks WHERE service=? AND ok=1", (svc,));  s = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM restarts WHERE service=?", (svc,));         r = c.fetchone()[0]
            c.execute("SELECT ok, ts FROM checks WHERE service=? ORDER BY ts DESC LIMIT 1", (svc,))
            last = c.fetchone()
            u = round(s / t * 100, 1) if t > 0 else 0.0
            services.append({
                "name": svc, "total": t, "success": s, "failed": t - s,
                "restarts": r, "uptime": u,
                "is_up": bool(last and last["ok"] == 1),
                "last_check": last["ts"][11:19] if last else "--"
            })

        c.execute("SELECT failure_type, COUNT(*) as cnt FROM checks WHERE failure_type != 'NONE' GROUP BY failure_type ORDER BY cnt DESC")
        failure_types = [{"type": r["failure_type"], "count": r["cnt"]} for r in c.fetchall()]
        if not failure_types:
            failure_types = [{"type": "ALL HEALTHY", "count": total}]

        trend = {"labels": []}
        for svc in services_list:
            c.execute("SELECT ok, ts FROM checks WHERE service=? ORDER BY ts DESC LIMIT 60", (svc,))
            rows = list(reversed(c.fetchall()))
            trend[svc] = []
            window = 10
            for i in range(len(rows)):
                batch = rows[max(0, i-window):i+1]
                pct = round(sum(1 for r in batch if r["ok"]==1) / len(batch) * 100, 1) if batch else 0
                trend[svc].append(pct)
            if not trend["labels"] and rows:
                trend["labels"] = [r["ts"][11:19] for r in rows]

        c.execute("SELECT ts, service, reason FROM restarts ORDER BY ts DESC LIMIT 10")
        recent_restarts = [dict(r) for r in c.fetchall()]

        c.execute("SELECT ts, service, ok, failure_type FROM checks ORDER BY ts DESC LIMIT 15")
        recent_checks = [dict(r) for r in c.fetchall()]

        try:
            c.execute("SELECT COUNT(*) FROM email_logs");  email_total = c.fetchone()[0]
            c.execute("SELECT ts, service, reason, recipient, status FROM email_logs ORDER BY ts DESC LIMIT 20")
            email_logs = [dict(r) for r in c.fetchall()]
        except:
            email_total = 0
            email_logs  = []

        conn.close()

        return jsonify({
            "total": total, "success": success, "fail": fail,
            "restarts": restarts, "uptime": uptime,
            "services": services, "failure_types": failure_types,
            "trend": trend, "recent_restarts": recent_restarts,
            "recent_checks": recent_checks,
            "email_logs": email_logs, "email_total": email_total
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=8081, debug=True)