import asyncio
from flask import Blueprint, jsonify
from agent_docs import policy_evaluation 

dashboard_bp = Blueprint("dashboard", __name__)


WHISTLE_FILE = "whistleblower_reports.json"

EVAL_CACHE = {
    "results": None,
    "last_updated": None
}
def load_whistleblower_stats():
    """Count number of reports per forest."""
    if not os.path.exists(WHISTLE_FILE):
        return {}

    with open(WHISTLE_FILE, "r") as f:
        reports = json.load(f)

    forests = [r.get("forest", "Unknown") for r in reports]
    return dict(Counter(forests))

@dashboard_bp.route("/policy-results", methods=["GET"])
def get_policy_results():
    if EVAL_CACHE["results"] is not None:
        return jsonify({
            "results": EVAL_CACHE["results"],
            "cached": True,
            "last_updated": EVAL_CACHE["last_updated"],
            "whistleblower_stats": load_whistleblower_stats()   # NEW LINE
        }), 200

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        model_output = loop.run_until_complete(policy_evaluation())

        from datetime import datetime
        EVAL_CACHE["results"] = model_output
        EVAL_CACHE["last_updated"] = datetime.utcnow().isoformat()

        return jsonify({
            "results": model_output,
            "cached": False,
            "last_updated": EVAL_CACHE["last_updated"],
            "whistleblower_stats": load_whistleblower_stats()   # NEW LINE
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
