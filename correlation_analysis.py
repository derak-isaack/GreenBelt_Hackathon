import pandas as pd
import requests
import numpy as np
from scipy.stats import pearsonr
# import matplotlib.pyplot as plt
import statsmodels.api as sm

def load_ndvi_data(filepath):
    """
    Load NDVI data from CSV, calculate NDVI from B4 and B5 bands, and aggregate to yearly means.
    NDVI is used as a proxy for biomass.
    """
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    df['ndvi'] = (df['B5_mean'] - df['B4_mean']) / (df['B5_mean'] + df['B4_mean'])
    df['year'] = df['date'].dt.year
    yearly_ndvi = df.groupby('year')['ndvi'].mean().reset_index()
    return yearly_ndvi

def fetch_gdp_data(country_code='KEN', start_year=2013, end_year=2024):
    """
    Fetch GDP data from World Bank API for the specified country and years.
    """
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD?format=json&date={start_year}:{end_year}"
    response = requests.get(url)
    data = response.json()
    gdp_data = []
    for item in data[1]:
        if item['value'] is not None:
            gdp_data.append({
                'year': int(item['date']),
                'gdp': item['value']
            })
    df_gdp = pd.DataFrame(gdp_data)
    return df_gdp

def correlate_ndvi_gdp(ndvi_df, gdp_df):
    """
    Merge NDVI and GDP data and compute Pearson correlation.
    """
    merged = pd.merge(ndvi_df, gdp_df, on='year')
    if len(merged) > 1:
        corr, p_value = pearsonr(merged['ndvi'], merged['gdp'])
    else:
        corr, p_value = np.nan, np.nan
    return corr, p_value, merged

def regression_analysis(ndvi_df, gdp_df):
    """
    Perform linear regression to quantify the effect of NDVI (biomass proxy) on GDP.
    This can help quantify the economic effects of forest encroachment (which reduces NDVI/biomass).
    """
    merged = pd.merge(ndvi_df, gdp_df, on='year')
    if len(merged) > 1:
        X = merged['ndvi']
        y = merged['gdp']
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        return model.summary()
    else:
        return "Insufficient data for regression"

def predict_gdp_from_ndvi(ndvi_df, gdp_df, ndvi_value):
    """
    Predict GDP impact based on NDVI input using the regression model.
    Returns the predicted GDP value.
    """
    merged = pd.merge(ndvi_df, gdp_df, on='year')
    if len(merged) > 1:
        X = merged['ndvi']
        y = merged['gdp']
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        # Predict for the given NDVI value
        prediction = model.predict([1, ndvi_value])  
        return float(prediction[0])
    else:
        return None

def main():
    # Load NDVI data (proxy for biomass)
    ndvi_data = load_ndvi_data('SentinelMakueni.csv')

    # Fetch economic data (GDP)
    gdp_data = fetch_gdp_data()

    # Compute correlation
    corr, p, merged = correlate_ndvi_gdp(ndvi_data, gdp_data)
    print(f"Pearson Correlation between NDVI and GDP: {corr}")
    print(f"P-value: {p}")

    # Regression analysis
    summary = regression_analysis(ndvi_data, gdp_data)
    print("Regression Summary:")
    print(summary)

    # Print the merged data for inspection
    if not merged.empty:
        print("Merged NDVI and GDP data:")
        print(merged)
    else:
        print("No overlapping data to analyze")
