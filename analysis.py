import pandas as pd
import numpy as np
from flask import Blueprint, jsonify

ndvi_bp = Blueprint("ndvi", __name__)


df = pd.read_csv("SentinelMakueni.csv")  

df_new = df.copy()
df_new.drop(columns=['interpolated_flag', '.geo', 'image_count', 'system:index', 'orbit','relative_orbit'],
            inplace=True, errors="ignore")


df_new["date"] = pd.to_datetime(df_new["date"])
df_new["month"] = df_new["date"].dt.month
df_new["year"] = df_new["date"].dt.year


def compute_s1_features(df):
    df["VV"] = df["VV"].replace([np.inf, -np.inf], np.nan).fillna(0)
    df["VH"] = df["VH"].replace([np.inf, -np.inf], np.nan).fillna(0)

    df["VH_VV_ratio"] = np.where(df["VV"] != 0, df["VH"] / df["VV"], 0)

    df["RVI"] = np.where((df["VV"] + df["VH"]) != 0,
                         4 * df["VH"] / (df["VV"] + df["VH"]),
                         0)

    df["RFDI"] = np.where((df["VV"] + df["VH"]) != 0,
                          (df["VV"] - df["VH"]) / (df["VV"] + df["VH"]),
                          0)

    return df

df_new = compute_s1_features(df_new)

@ndvi_bp.route("/api/s1/trend", methods=["GET"])
def s1_trend():
    result = df_new.to_dict(orient="records")
    return jsonify(result)
