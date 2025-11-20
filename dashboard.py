import os
import json
import asyncio
from collections import Counter
from flask import Blueprint, jsonify, request
from agent_docs import policy_evaluation
import jwt
from datetime import datetime
from correlation_analysis import load_ndvi_data, fetch_gdp_data, correlate_ndvi_gdp, regression_analysis, predict_gdp_from_ndvi

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

        # Compute correlation analysis
        try:
            ndvi_data = load_ndvi_data('makueni_bands.csv')
            gdp_data = fetch_gdp_data()
            corr, p_value, merged_df = correlate_ndvi_gdp(ndvi_data, gdp_data)
            regression_summary = regression_analysis(ndvi_data, gdp_data)
            correlation_results = {
                "correlation_coefficient": corr,
                "p_value": p_value,
                "merged_data": merged_df.to_dict('records') if not merged_df.empty else [],
                "regression_summary": str(regression_summary)
            }
        except Exception as e:
            correlation_results = {"error": str(e)}

        EVAL_CACHE["results"] = model_output
        EVAL_CACHE["correlation_analysis"] = correlation_results
        EVAL_CACHE["last_updated"] = datetime.utcnow().isoformat()

    response = {
        "results": EVAL_CACHE["results"],
        "correlation_analysis": EVAL_CACHE.get("correlation_analysis", {}),
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


# -----------------------
#   NDVI PREDICTION ENDPOINT
# -----------------------
@dashboard_bp.route("/ndvi/predict", methods=["POST"])
def predict_ndvi_impact():
    """
    Predict GDP impact based on NDVI value.
    Expects JSON with 'ndvi' field.
    """
    try:
        data = request.get_json()
        if not data or 'ndvi' not in data:
            return jsonify({"error": "NDVI value is required"}), 400

        ndvi_value = float(data['ndvi'])
        if not (-1 <= ndvi_value <= 1):
            return jsonify({"error": "NDVI value must be between -1 and 1"}), 400

        ndvi_data = load_ndvi_data('makueni_bands.csv')
        gdp_data = fetch_gdp_data()

        predicted_gdp = predict_gdp_from_ndvi(ndvi_data, gdp_data, ndvi_value)
        if predicted_gdp is None:
            return jsonify({"error": "Insufficient data for prediction"}), 400

        return jsonify({"predicted_gdp": predicted_gdp}), 200

    except ValueError as e:
        return jsonify({"error": "Invalid NDVI value"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
