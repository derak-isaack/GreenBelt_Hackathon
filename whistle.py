from flask import Blueprint, request, jsonify
import uuid
import datetime
import json
import os

whistle_bp = Blueprint("whistleblower", __name__)

# Storage for anonymous reports
STORAGE_FILE = "whistleblower_reports.json"


def save_report(data):
    """Save whistleblower report into JSON storage."""
    if not os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "w") as f:
            json.dump([], f)

    with open(STORAGE_FILE, "r") as f:
        reports = json.load(f)

    reports.append(data)

    with open(STORAGE_FILE, "w") as f:
        json.dump(reports, f, indent=4)


@whistle_bp.route("/submit", methods=["POST"])
def submit_report():
    payload = request.get_json()

    if not payload:
        return jsonify({"error": "Missing report payload"}), 400

    report_text = payload.get("report", "")
    attachments = payload.get("attachments", [])
    forest = payload.get("forest")  # NEW FIELD

    if not report_text:
        return jsonify({"error": "Report text is required"}), 400

    if not forest:
        return jsonify({"error": "Forest name is required"}), 400

    report_data = {
        "id": str(uuid.uuid4()),
        "report": report_text,
        "attachments": attachments,
        "forest": forest,   # SAVE HERE
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "status": "received"
    }

    save_report(report_data)

    return jsonify({
        "message": "Report submitted anonymously.",
        "reference_id": report_data["id"]
    }), 200
