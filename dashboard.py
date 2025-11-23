import os
import json
import asyncio
from collections import Counter
from flask import Blueprint, jsonify, request
from agent_docs import policy_evaluation
import jwt
from datetime import datetime
from correlation_analysis import load_ndvi_data, fetch_gdp_data, correlate_ndvi_gdp, regression_analysis, predict_gdp_from_ndvi
import pandas as pd
import numpy as np

dashboard_bp = Blueprint("dashboard", __name__)

SECRET_KEY = os.getenv("JWT_SECRET", "CHANGE_THIS_SECRET")

WHISTLE_FILE = "whistleblower_reports.json"

EVAL_CACHE = {
    "results": None,
    "last_updated": None
}

# Load and process Sentinel data
df = pd.read_csv("SentinelMakueni.csv")

frames = []
for forest in df['forest'].unique():
    sub = df[df['forest'] == forest].sort_values('date')

    sub = sub.drop_duplicates(subset='date')

    sub['VH'] = sub['VH'].interpolate(method='linear', limit_direction='both')

    frames.append(sub)

df_clean = pd.concat(frames, ignore_index=True)

df_clean.to_csv("Makueni_interpolated.csv", index=False)

df_new = df_clean.copy()
df_new.drop(columns=['interpolated_flag', '.geo', 'image_count', 'system:index', 'orbit','relative_orbit'],
            inplace=True, errors="ignore")

df_new["date"] = pd.to_datetime(df_new["date"])
df_new["month"] = df_new["date"].dt.month
df_new["year"] = df_new["date"].dt.year

def compute_s1_features(df):
    df["VV"] = df["VV"].replace([np.inf, -np.inf], np.nan).fillna(0)
    df["VH"] = df["VH"].replace([np.inf, -np.inf], np.nan).fillna(0)

    df["VV_lin"] = 10 ** (df["VV"] / 10)
    df["VH_lin"] = 10 ** (df["VH"] / 10)

    df["VH_VV_ratio"] = np.where(df["VV_lin"] != 0, df["VH_lin"] / df["VV_lin"], 0)

    df["RVI"] = np.where((df["VV_lin"] + df["VH_lin"]) != 0,
                          4 * df["VH_lin"] / (df["VV_lin"] + df["VH_lin"]),
                          0)

    df["RFDI"] = np.where((df["VV_lin"] + df["VH_lin"]) != 0,
                           (df["VV_lin"] - df["VH_lin"]) / (df["VV_lin"] + df["VH_lin"]),
                           0)
    df['alert'] = np.where(df['RFDI'] > 0.61, 1, 0)

    return df

df_new = compute_s1_features(df_new)


# -----------------------
#   GET USER ROLE FROM JWT
# -----------------------
def get_user_role():
    auth_header = request.headers.get("Authorization", "")
    print(f"Dashboard get_user_role: auth_header present: {bool(auth_header)}")

    if not auth_header or " " not in auth_header:
        print("Dashboard get_user_role: No valid auth header")
        return None

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        role = payload.get("role")
        print(f"Dashboard get_user_role: decoded role: {role}")
        return role
    except Exception as e:
        print(f"Dashboard get_user_role: JWT decode error: {e}")
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
    print("DEBUG: get_policy_results called")

    role = get_user_role()
    print(f"DEBUG: user role: {role}")

    if role not in ["admin", "researcher"]:
        print("DEBUG: unauthorized access")
        return jsonify({"error": "Unauthorized"}), 403

    # Run evaluation or use cache
    if EVAL_CACHE["results"] is None:
        print("DEBUG: cache empty, running policy evaluation")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print("DEBUG: calling policy_evaluation")
            model_output = loop.run_until_complete(policy_evaluation())
            print("DEBUG: policy_evaluation completed successfully")
        except Exception as e:
            print(f"DEBUG: policy_evaluation failed: {e}")
            return jsonify({"error": f"Policy evaluation failed: {str(e)}"}), 500

        # Compute correlation analysis
        print("DEBUG: starting correlation analysis")
        try:
            print("DEBUG: loading NDVI data")
            ndvi_data = load_ndvi_data('makueni_bands.csv')
            print(f"DEBUG: NDVI data loaded, shape: {ndvi_data.shape}")
            print("DEBUG: fetching GDP data")
            gdp_data = fetch_gdp_data()
            print(f"DEBUG: GDP data loaded, shape: {gdp_data.shape}")
            print("DEBUG: correlating NDVI and GDP")
            corr, p_value, merged_df = correlate_ndvi_gdp(ndvi_data, gdp_data)
            print(f"DEBUG: correlation: {corr}, p_value: {p_value}")
            print("DEBUG: running regression analysis")
            regression_summary = regression_analysis(ndvi_data, gdp_data)
            print("DEBUG: regression completed")
            correlation_results = {
                "correlation_coefficient": corr,
                "p_value": p_value,
                "merged_data": merged_df.to_dict('records') if not merged_df.empty else [],
                "regression_summary": str(regression_summary)
            }
        except Exception as e:
            print(f"DEBUG: correlation analysis failed: {e}")
            correlation_results = {"error": str(e)}

        EVAL_CACHE["results"] = model_output
        EVAL_CACHE["correlation_analysis"] = correlation_results
        EVAL_CACHE["last_updated"] = datetime.utcnow().isoformat()
        print("DEBUG: cache updated")

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


# -----------------------
#   FILTERED DATA ENDPOINT
# -----------------------
@dashboard_bp.route("/filtered-data", methods=["GET"])
def get_filtered_data():
    """
    Get filtered Sentinel-1 data with alerts based on RFDI threshold.
    Accepts query parameters: forest, year, month
    Returns filtered data and alert count.
    """
    try:
        # Get filter parameters
        forest_filter = request.args.get("forest")
        year_filter = request.args.get("year")
        month_filter = request.args.get("month")

        # Start with full dataset
        df_filtered = df_new.copy()

        # Apply filters
        if forest_filter:
            df_filtered = df_filtered[df_filtered["forest"] == forest_filter]
        if year_filter:
            df_filtered = df_filtered[df_filtered["year"] == int(year_filter)]
        if month_filter:
            df_filtered = df_filtered[df_filtered["month"] == int(month_filter)]

        # Sort by date
        df_filtered = df_filtered.sort_values("date")

        # Compute alert count
        alert_count = int(df_filtered['alert'].sum())

        # Convert to JSON-ready dict
        result_data = df_filtered.to_dict(orient="records")

        # Return filtered data and alert count
        return jsonify({
            "data": result_data,
            "alert_count": alert_count,
            "total_records": len(result_data),
            "filters_applied": {
                "forest": forest_filter,
                "year": year_filter,
                "month": month_filter
            }
        }), 200

    except ValueError as e:
        return jsonify({"error": "Invalid filter parameter value"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
