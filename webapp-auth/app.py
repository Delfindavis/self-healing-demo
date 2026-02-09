from flask import Flask

app = Flask(__name__)

@app.route("/")
def auth():
    return "<h2>Authentication Service</h2><p>Login & user validation module</p>"

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
