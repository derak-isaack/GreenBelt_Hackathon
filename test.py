import pandas as pd
import numpy as np  

# df = pd.read_csv("SentinelMakueni.csv")
# print(df)
# group = df.groupby(['year', 'month']).agg({'RFDI': 'mean'}).reset_index().sort_values(['year', 'month'])

# print(group)
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
print(df_new)