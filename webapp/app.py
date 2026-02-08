from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "App is running"

@app.route("/health")
def health():
    return "OK", 200

app.run(host="0.0.0.0", port=5000)
