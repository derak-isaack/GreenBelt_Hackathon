import pandas as pd
import numpy as np
from flask import Blueprint, jsonify, request 

ndvi_bp = Blueprint("ndvi", __name__)


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

    df["VH_VV_ratio"] = np.where(df["VV"] != 0, df["VH"] / df["VV"], 0)

    df["RVI"] = np.where((df["VV"] + df["VH"]) != 0,
                         4 * df["VH"] / (df["VV"] + df["VH"]),
                         0)

    df["RFDI"] = np.where((df["VV"] + df["VH"]) != 0,
                          (df["VV"] - df["VH"]) / (df["VV"] + df["VH"]),
                          0)
    df['alert'] = np.where(df['RFDI'] > 0.3, 1, 0) 


    return df 

df_new = compute_s1_features(df_new)

@ndvi_bp.route("/api/s1/trend", methods=["GET"])
def s1_trend():
    # result = df_new.to_dict(orient="records")
    # return jsonify(result)
    forest_filter = request.args.get("forest")   
    year_filter = request.args.get("year")       
    month_filter = request.args.get("month")     

    df_filtered = df_new.copy()

    if forest_filter:
        df_filtered = df_filtered[df_filtered["forest"] == forest_filter]
    if year_filter:
        df_filtered = df_filtered[df_filtered["year"] == int(year_filter)]
    if month_filter:
        df_filtered = df_filtered[df_filtered["month"] == int(month_filter)]

    # Sort by date
    df_filtered = df_filtered.sort_values("date")

    # Convert to JSON-ready dict
    result = df_filtered.to_dict(orient="records")
    return jsonify(result)
