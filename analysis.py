import pandas as pd
import numpy as np
import os
import logging
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

if not os.path.exists("Makueni_interpolated.csv"):
    try:
        df_clean.to_csv("Makueni_interpolated.csv", index=False)
    except PermissionError:
        logging.warning("Permission denied when writing Makueni_interpolated.csv")

df_new = df_clean.copy()
df_new.drop(columns=['interpolated_flag', '.geo', 'image_count', 'system:index', 'orbit','relative_orbit'],
            inplace=True, errors="ignore")


df_new["date"] = pd.to_datetime(df_new["date"])
df_new["month"] = df_new["date"].dt.month 
df_new["year"] = df_new["date"].dt.year
VV_lin = 10 ** (df["VV"] / 10)
VH_lin = 10 ** (df["VH"] / 10)


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

monthly_rfdi = df_new.groupby(['year', 'month']).agg({
    'RFDI': 'mean',
    'alert': 'sum'
}).reset_index().sort_values(['year', 'month'])

monthly_ndvi = monthly_rfdi.copy()

@ndvi_bp.route("/api/s1/trend", methods=["GET"])
def s1_trend():
    forests_param = request.args.get("forests") or request.args.get("forest")  # support both for backward compatibility
    year_filter = request.args.get("year")
    month_filter = request.args.get("month")
    print("request.args:", request.args)

    df_filtered = df_new.copy()
    print("DataFrame length before filtering:", len(df_new))

    selected_forests = None
    if forests_param:
        if "," in forests_param:
            selected_forests = [f.strip() for f in forests_param.split(",") if f.strip()]
            df_filtered = df_filtered[df_filtered["forest"].isin(selected_forests)]
        else:
            # single forest
            df_filtered = df_filtered[df_filtered["forest"] == forests_param]
            selected_forests = [forests_param]

    if year_filter:
        df_filtered = df_filtered[df_filtered["year"] == int(year_filter)]
    if month_filter:
        df_filtered = df_filtered[df_filtered["month"] == int(month_filter)]

    print("DataFrame length after filtering:", len(df_filtered))

    if selected_forests and len(selected_forests) > 1:
        # Multiple forests: aggregate by year, month, forest
        df_aggregated = df_filtered.groupby(['year', 'month', 'forest']).agg({'RFDI': 'mean'}).reset_index().sort_values(['forest', 'year', 'month'])
    else:
        # Single forest or all: aggregate by year and month
        df_aggregated = df_filtered.groupby(['year', 'month']).agg({'RFDI': 'mean'}).reset_index().sort_values(['year', 'month'])

    # Convert to JSON-ready dict
    result = df_aggregated.to_dict(orient="records")
    return jsonify(result)
