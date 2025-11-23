import os
import logging
import asyncio
import pandas as pd
from textwrap import shorten
from google import genai
from analysis import df_new, monthly_ndvi

MAX_CONTEXT_CHARS = 50_000


# ==========================
# LOAD DRIVERS CSV
# ==========================
def load_forest_loss_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Drivers CSV not found: {path}")
    df = pd.read_csv(path)
    return df


# ==========================
# BUILD COMBINED CONTEXT
# ==========================
def build_combined_context(df, monthly_ndvi, drivers_df) -> str:
    parts = []

    # ==== RFDI CSV SUMMARY ====
    try:
        head_csv = df.head(20).to_csv(index=False)
    except Exception as e:
        head_csv = f"<ERROR_SERIALIZING_CSV: {e}>"

    parts.append("=== SATELLITE DERIVED RFDI SUMMARY ===")
    parts.append(f"Columns: {', '.join(list(df.columns))}")
    parts.append(f"Rows: {len(df)}")
    parts.append("Sample rows (up to 20):")
    parts.append(head_csv)

    # ==== RFDI TRENDS ====
    parts.append("\n=== MONTHLY RFDI TRENDS ===")
    parts.append(f"Columns: {', '.join(list(monthly_ndvi.columns))}")
    parts.append(f"Rows: {len(monthly_ndvi)}")

    try:
        ndvi_csv = monthly_ndvi.to_csv(index=False)
        parts.append("Monthly RFDI values:")
        parts.append(ndvi_csv)
    except Exception as e:
        parts.append(f"<ERROR_SERIALIZING_RFDI: {e}>")

    # ==== FOREST LOSS DRIVERS ====
    parts.append("\n=== FOREST LOSS DRIVERS DATA (CSV) ===")
    parts.append(f"Columns: {', '.join(list(drivers_df.columns))}")
    parts.append(f"Rows: {len(drivers_df)}")

    try:
        drivers_csv = drivers_df.head(30).to_csv(index=False)
        parts.append("Sample forest loss drivers (up to 30 rows):")
        parts.append(drivers_csv)
    except Exception as e:
        parts.append(f"<ERROR_SERIALIZING_DRIVERS_CSV: {e}>")

    combined = "\n\n".join(parts)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[: MAX_CONTEXT_CHARS - 200] + "\n\n...[TRUNCATED]..."

    return combined


async def policy_evaluation(forest=None):
    if not forest:
        return "Please select a forest to generate the policy evaluation."

    # Filter df_new for the selected forest
    df_new_filtered = df_new[df_new['forest'] == forest]
    if df_new_filtered.empty:
        return f"No data available for the selected forest: {forest}"

    # Recompute monthly_ndvi for the filtered data
    monthly_ndvi_filtered = df_new_filtered.groupby(['year', 'month']).agg({
        'RFDI': 'mean',
        'alert': 'sum'
    }).reset_index().sort_values(['year', 'month'])

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    drivers_df = load_forest_loss_csv("tree_cover_loss_by_driver.csv")

    data_context = build_combined_context(df_new_filtered, monthly_ndvi_filtered, drivers_df)

    task_text = (
    "You are an environmental policy analyst. Using the following data sources:\n"
    "- Sentinel-1 satellite-based RVI/RFDI/VV/VH vegetation condition trends for a semi-arid area\n"
    "- A CSV showing forest loss drivers, loss year, loss area (ha), and gross carbon emissions (Mg)\n\n"
    "Prepare a clear, concise, and professional policy advocacy report for community Forest organizations. The report should be "
    "manager-friendly, free of technical jargon, and easy to read.\n\n"

    "Your tasks:\n"
    "1. Identify the main drivers of forest loss, grouped by year.\n"
    "2. Summarize the total forest area lost and total carbon emissions caused by each driver.\n"
    "3. Interpret how these drivers are reflected in RFDI trends, with emphasis on forest health.\n"
    "4. Provide a simple narrative describing how activities such as logging, permanent agriculture, "
    "and other pressures weaken forest ecosystems.\n"
    "5. Identify which drivers create the largest environmental impact on community forests.\n"
    "6. Present a clear table with:\n"
    "     - Forest Loss Driver\n"
    "     - Evidence from CSV (loss area and carbon emissions)\n"
    "     - Observed RVI/RFDI/VV/VH Pattern\n"
    "     - Environmental Impact Summary\n"
    "     - Policy Actions Needed\n"
    "7. Provide actionable, practical policy recommendations aimed at RESTORING and STRENGTHENING community forests. "
    "These recommendations should specifically apply to forests dominated by pine, cypress, riverine species, "
    "eucalyptus, grevillea, and indigenous trees.\n"
    "8. Include ecosystem-building strategies and policies geared towards:\n"
    "     - Reforestation and enrichment planting\n"
    "     - Native species recovery\n"
    "     - Community-led forest stewardship\n"
    "     - Landscape-level restoration\n"
    "     - Agroforestry integration\n"
    "     - Sustainable harvesting and controlled use zones\n"
    "     - Fire and invasive-species management\n"
    "9. Provide community-level recommendations that local leaders can easily implement.\n"
    "10. Use clear and accessible language suitable for senior managers and policymakers.\n"
    "11. Explain (in simple terms) how addressing key forest loss drivers will improve RFDI and RVI signals "
    "and lead to healthier forest ecosystems.\n\n"
    "Avoid unnecessary technical language. Avoid fabricated or speculative details. Keep all observations "
    "grounded in the provided CSV data and RVI/VV/VH/RFDI trends.\n\n"
    f"=== ANALYSIS CONTEXT ===\n{data_context}"
) 



    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=task_text
        )
        return response.text

    except Exception as e:
        logging.error(f"Error in policy_evaluation: {e}")
        return "Error: Unable to generate policy evaluation due to API failure."


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    result = asyncio.run(policy_evaluation())
    print("\n=== POLICY ADVOCACY REPORT ===\n")
    print(result)
