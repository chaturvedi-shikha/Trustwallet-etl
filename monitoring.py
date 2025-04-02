from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Pipeline is running"}), 200

@app.route("/metrics", methods=["GET"])
def get_metrics():
    """Metrics for monitoring"""
    log_size = os.path.getsize("logs/etl.log") if os.path.exists("logs/etl.log") else 0
    return jsonify({
        "log_file_size": log_size,
        "database_status": "connected",  # Mocked status
        "api_status": "active",  # Mocked status
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
