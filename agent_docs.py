import os
import logging
import asyncio
import re
from textwrap import shorten
from pypdf import PdfReader
# import google.generativeai as genai
from google import genai
from dateutil import parser as date_parser
from analysis import df_new, monthly_ndvi


MAX_CONTEXT_CHARS = 50_000
PDF_CHUNK_SNIPPET = 10_000


def extract_pdf_text(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")
    reader = PdfReader(path)
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            continue
    text = "\n".join(pages)
    return " ".join(text.split())


def extract_dates(text: str) -> list:
    # Regex for dates: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, etc.
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
    ]
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    # Try to parse and deduplicate
    parsed_dates = set()
    for date_str in dates:
        try:
            parsed = date_parser.parse(date_str)
            parsed_dates.add(parsed.strftime('%Y-%m-%d'))
        except:
            parsed_dates.add(date_str)
    return list(parsed_dates)


def extract_monetary_figures(text: str) -> list:
    money_patterns = [
        r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  
        r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:million|billion|thousand|M|B|K)\b',  
        r'\b(?:KSh|KES|USD|EUR|GBP)\s*\d+(?:,\d{3})*(?:\.\d{2})?\b',  
        r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:KSh|KES|USD|EUR|GBP)\b'  
    ]
    figures = []
    for pattern in money_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        figures.extend(matches)
    return list(set(figures))


def extract_budgets(text: str) -> list:
    budget_keywords = r'\b(?:budget|allocated|set aside|funds|appropriation|expenditure|cost|expense)\b'
    amount_patterns = r'\d+(?:,\d{3})*(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?'
    budget_pattern = rf'{budget_keywords}.*?({amount_patterns})'
    budgets = re.findall(budget_pattern, text, re.IGNORECASE | re.DOTALL)
    return list(set(budgets))


def extract_pdf_data(path: str) -> dict:
    text = extract_pdf_text(path)
    return {
        'dates': extract_dates(text),
        'monetary_figures': extract_monetary_figures(text),
        'budgets': extract_budgets(text),
        'full_text': text
    }


def calculate_total_set_aside(pdf_data_list: list) -> float:
    total = 0.0
    for pdf_data in pdf_data_list:
        for budget in pdf_data['budgets']:
            # Extract number from budget string
            num_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', budget)
            if num_match:
                num_str = num_match.group(1).replace(',', '')
                try:
                    amount = float(num_str)
                    # Check for multipliers
                    if 'million' in budget.lower() or 'M' in budget:
                        amount *= 1_000_000
                    elif 'billion' in budget.lower() or 'B' in budget:
                        amount *= 1_000_000_000
                    elif 'thousand' in budget.lower() or 'K' in budget:
                        amount *= 1_000
                    total += amount
                except ValueError:
                    continue
    return total


def build_combined_context(df, monthly_ndvi, pdf_paths: dict) -> str:
    parts = []
    pdf_data_list = []

    try:
        head_csv = df.head(20).to_csv(index=False)
    except Exception as e:
        head_csv = f"<ERROR_SERIALIZING_CSV: {e}>"

    parts.append("=== CSV SUMMARY ===")
    parts.append(f"Columns: {', '.join(list(df.columns))}")
    parts.append(f"Rows: {len(df)}")
    parts.append("Sample rows (up to 20):")
    parts.append(head_csv)

    parts.append("=== NDVI TRENDS ===")
    parts.append(f"Columns: {', '.join(list(monthly_ndvi.columns))}")
    parts.append(f"Rows: {len(monthly_ndvi)}")
    try:
        ndvi_csv = monthly_ndvi.to_csv(index=False)
        parts.append("Monthly NDVI data:")
        parts.append(ndvi_csv)
    except Exception as e:
        parts.append(f"<ERROR_SERIALIZING_NDVI: {e}>")

    for name, path in pdf_paths.items():
        try:
            pdf_data = extract_pdf_data(path)
            pdf_data_list.append(pdf_data)
            txt = pdf_data['full_text']
            snippet = shorten(txt, width=PDF_CHUNK_SNIPPET,
                              placeholder=" ...[truncated]...")
            parts.append(f"=== PDF: {name} ({os.path.basename(path)}) ===")
            parts.append(f"Dates found: {', '.join(pdf_data['dates'][:10])}")  
            parts.append(f"Monetary figures: {', '.join(pdf_data['monetary_figures'][:10])}")
            parts.append(f"Budgets: {', '.join(pdf_data['budgets'][:10])}")
            parts.append("Content snippet:")
            parts.append(snippet)
        except Exception as e:
            parts.append(f"=== PDF: {name} ===\n<ERROR: {e}>")

    # Calculate total set aside
    total_set_aside = calculate_total_set_aside(pdf_data_list)
    parts.append(f"=== TOTAL SET ASIDE ===\nEstimated total funds set aside: ${total_set_aside:,.2f}")

    combined = "\n\n".join(parts)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[: MAX_CONTEXT_CHARS - 200] + "\n\n...[TRUNCATED]..."

    return combined


async def policy_evaluation():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # Note: Ensure GEMINI_API_KEY is set in .env
    # model = genai.GenerativeModel("gemini-1.5-flash")

    pdfs = {
        "FOLAREP": "Makueni-FOLAREP.pdf",
    }

    data_context = build_combined_context(df_new, monthly_ndvi, pdfs)

    task_text = (
        "You are a policy effectiveness evaluator. Using the CSV data containing "
        "monthly RFDI measurements derived from satellite data, "
        "and the RFDI trends data, along with the FOLAREP PDF document, perform:\n\n"
        "1. Focus on the FOLAREP PDF's SWOT, PESTEL, and Risk Analysis sections for Makueni County restoration.\n"
        "2. Extract key findings from the Risk Analysis section, noting that the biggest risk to reforestation is encroachment.\n"
        "3. Extract key findings from the PESTEL analysis, noting that the biggest threats are information barriers and conflicting government policies.\n"
        "4. Examine RFDI trends in the CSV and alerts data to assess current forest health.\n"
        "5. Assess policy effectiveness against RFDI data to determine if observed data shows policies are achieving goals.\n"
        "6. Highlight correlations between proposed actions in FOLAREP and observed RFDI trends.\n"
        "7. Present a structured table with:\n"
        "   - Proposed Step (from FOLAREP)\n"
        "   - Evidence from PDFs / CSV\n"
        "   - Observed RFDI Outcome\n"
        "   - Effectiveness Assessment\n"
        "8. Provide recommendations for policies that are not achieving desired results.\n"
        "9. Provide layman-friendly explanations of the key findings, avoiding technical jargon where possible.\n"
        "10. Quantify the economic and governmental impacts of RFDI declines on national and county levels, including potential revenue losses and costs to governments.\n"
        "11. Based on the analysis, provide actionable policy recommendations to mitigate forest encroachment and improve RFDI trends.\n"
        "12. Analyze the extracted dates, monetary figures, and budgets from the FOLAREP PDF.\n"
        "13. Calculate and report the total funds set aside based on the budget extractions.\n"
        "14. Propose specific cost-saving measures based on RFDI trends and policy effectiveness analysis. Identify areas where current spending is inefficient and suggest reallocations or reductions that could improve forest health outcomes.\n\n"
        f"=== DATA CONTEXT ===\n{data_context}"
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


if __name__ == "__main__":
    result = asyncio.run(policy_evaluation())
    print("\n=== POLICY EVALUATION REPORT ===\n")
    print(result)

