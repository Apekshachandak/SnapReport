"""
app.py — Flask web UI for SnapReport.
Routes:
  GET  /          -> ZIP + agent input form
  POST /generate  -> run pipeline, return PDF download
  GET  /health    -> { "status": "ok" }
"""

import os
from flask import Flask, render_template, request, send_file, jsonify
from main import run as run_pipeline

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    zip_code = request.form.get("zip", "").strip()

    if not zip_code or not zip_code.isdigit() or len(zip_code) != 5:
        return jsonify({"error": "Please enter a valid 5-digit US ZIP code."}), 400

    agent = {
        "name":    request.form.get("agent_name", "").strip(),
        "phone":   request.form.get("agent_phone", "").strip(),
        "email":   request.form.get("agent_email", "").strip(),
        "company": request.form.get("agent_company", "").strip(),
    }

    try:
        pdf_path = run_pipeline(zip_code, OUTPUT_DIR, agent=agent)
    except SystemExit:
        return jsonify({"error": "Report generation failed. Check your API keys or try a different ZIP code."}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF was not created. Check server logs."}), 500

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=os.path.basename(pdf_path),
        mimetype="application/pdf",
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
