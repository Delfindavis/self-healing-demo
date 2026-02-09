from flask import Flask

app = Flask(__name__)

@app.route("/")
def dashboard():
    return """
    <h1>Self-Healing Web Application Dashboard</h1>
    <ul>
        <li>Auth Service: RUNNING</li>
        <li>Payment Service: RUNNING</li>
        <li>Monitoring: ACTIVE</li>
    </ul>
    <p>All services are containerized and monitored.</p>
    """

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
