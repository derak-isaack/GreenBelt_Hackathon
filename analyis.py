import pandas as pd
import numpy as np
from flask import Blueprint, jsonify

ndvi_bp = Blueprint("ndvi", __name__)

df = pd.read_csv("makueni_bands.csv")

df_new = df.copy()
df_new.drop(columns=['interpolated_flag', '.geo', 'image_count', 'index'],
            inplace=True, errors="ignore")

# Convert date
df_new["date"] = pd.to_datetime(df_new["date"])
df_new["month"] = df_new["date"].dt.month
df_new["year"] = df_new["date"].dt.year

# Scale + NDVI function
def scale_and_compute_ndvi(df):
    scale = 2.75e-05  # Landsat scaling factor
    RED = df["B4_mean"] * scale
    NIR = df["B5_mean"] * scale

    df["B4_ref"] = RED
    df["B5_ref"] = NIR

    df["NDVI"] = (NIR - RED) / (NIR + RED)
    df["NDVI"] = df["NDVI"].replace([np.inf, -np.inf], np.nan).fillna(0)

    return df

df_new = scale_and_compute_ndvi(df_new)

# Monthly NDVI
monthly_ndvi = (
    df_new.groupby(["year", "month"])["NDVI"]
          .mean()
          .reset_index()
          .sort_values(["year", "month"])
)

@ndvi_bp.route("/api/ndvi/trend", methods=["GET"])
def ndvi_trend():
    result = monthly_ndvi.to_dict(orient="records")
    return jsonify(result)
