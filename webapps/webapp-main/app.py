from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

SERVICE_NAME = os.environ.get("SERVICE_NAME", "unknown-service")

system_status = {
    "healthy": True
}

@app.route("/")
def index():
    return f"""
    <h2>{SERVICE_NAME}</h2>
    <h3>Endpoints</h3>
    <ul>
        <li><a href="/health">/health</a></li>
        <li><a href="/crash">/crash</a></li>
        <li><a href="/slow">/slow</a></li>
        <li><a href="/toggle-health">/toggle-health</a></li>
    </ul>
    """

@app.route("/health")
def health():
    if system_status["healthy"]:
        return jsonify({"service": SERVICE_NAME, "status": "healthy", "timestamp": time.time()}), 200
    else:
        return jsonify({"service": SERVICE_NAME, "status": "unhealthy", "timestamp": time.time()}), 500

@app.route("/crash")
def crash():
    os._exit(1)

@app.route("/slow")
def slow():
    time.sleep(10)
    return "Slow response simulated", 200

@app.route("/toggle-health")
def toggle():
    system_status["healthy"] = not system_status["healthy"]
    state = "healthy" if system_status["healthy"] else "unhealthy"
    return jsonify({"service": SERVICE_NAME, "toggled_to": state})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)