import os
import json
import asyncio
from collections import Counter
from flask import Blueprint, jsonify, request
from agent_docs import policy_evaluation
import jwt
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__)

SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET")

WHISTLE_FILE = "whistleblower_reports.json"

EVAL_CACHE = {
    "results": None,
    "last_updated": None
}


# -----------------------
#   GET USER ROLE FROM JWT
# -----------------------
def get_user_role():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header or " " not in auth_header:
        return None

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("role")
    except Exception:
        return None


# -----------------------
#   LOAD WHISTLEBLOWER STATS
# -----------------------
def load_whistleblower_stats():
    if not os.path.exists(WHISTLE_FILE):
        return {}

    with open(WHISTLE_FILE, "r") as f:
        reports = json.load(f)

    forests = [r.get("forest", "Unknown") for r in reports]
    return dict(Counter(forests))


# -----------------------
#   POLICY RESULTS ENDPOINT
# -----------------------
@dashboard_bp.route("/policy-results", methods=["GET"])
def get_policy_results():

    role = get_user_role()

    if role not in ["admin", "researcher"]:
        return jsonify({"error": "Unauthorized"}), 403

    # Run evaluation or use cache
    if EVAL_CACHE["results"] is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        model_output = loop.run_until_complete(policy_evaluation())

        EVAL_CACHE["results"] = model_output
        EVAL_CACHE["last_updated"] = datetime.utcnow().isoformat()

    response = {
        "results": EVAL_CACHE["results"],
        "cached": True,
        "last_updated": EVAL_CACHE["last_updated"]
    }

    # -----------------------
    #   ROLE-BASED VISIBILITY
    # -----------------------

    # Admin sees whistleblower stats
    if role == "admin":
        response["whistleblower_stats"] = load_whistleblower_stats()

    # Researcher does NOT see whistleblower stats
    if role == "researcher":
        response["whistleblower_stats"] = None   # or simply omit the field entirely

    return jsonify(response), 200
