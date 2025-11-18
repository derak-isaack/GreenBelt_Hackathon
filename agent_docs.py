import os
import asyncio
from textwrap import shorten
from pypdf import PdfReader
from google import adk


from analyis import df   

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


def build_combined_context(df, pdf_paths: dict) -> str:
    parts = []
    try:
        head_csv = df.head(20).to_csv(index=False)
    except Exception as e:
        head_csv = f"<ERROR_SERIALIZING_CSV: {e}>"

    parts.append("=== CSV SUMMARY ===")
    parts.append(f"Columns: {', '.join(list(df.columns))}")
    parts.append(f"Rows: {len(df)}")
    parts.append("Sample rows (up to 20):")
    parts.append(head_csv)

    for name, path in pdf_paths.items():
        try:
            txt = extract_pdf_text(path)
            snippet = shorten(txt, width=PDF_CHUNK_SNIPPET,
                              placeholder=" ...[truncated]...")
            parts.append(f"=== PDF: {name} ({os.path.basename(path)}) ===")
            parts.append(snippet)
        except Exception as e:
            parts.append(f"=== PDF: {name} ===\n<ERROR: {e}>")

    combined = "\n\n".join(parts)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[: MAX_CONTEXT_CHARS - 200] + "\n\n...[TRUNCATED]..."

    return combined


async def policy_evaluation():
    client = adk.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    pdfs = {
        "Makueni County Bill": "makueniBill.pdf",
        "FOLAREP": "Makueni-FOLAREP.pdf",
    }

    data_context = build_combined_context(df, pdfs)

    task_text = (
        "You are a policy effectiveness evaluator. Using the CSV data containing "
        "monthly biomass and forest cover measurements derived from satellite data, "
        "and the two PDF documents (Makueni County Bill and FOLAREP), perform:\n\n"
        "1. Extract all mitigation steps, policies, or proposed actions from the PDFs.\n"
        "2. Examine biomass/forest cover trends in the CSV.\n"
        "3. For each step, determine if the observed data shows it is achieving its goals.\n"
        "4. Highlight correlations between proposed actions and observed improvements.\n"
        "5. Present a structured table with:\n"
        "   - Proposed Step\n"
        "   - Evidence from PDFs / CSV\n"
        "   - Observed Outcome\n"
        "   - Effectiveness Assessment\n\n"
        f"=== DATA CONTEXT ===\n{data_context}"
    )

    # google-adk is synchronous → run in executor to keep async clean
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.responses.create(
            model="gemini-2.0-flash",
            input=task_text
        )
    )

    return response.output_text


if __name__ == "__main__":
    result = asyncio.run(policy_evaluation())
    print("\n=== POLICY EVALUATION REPORT ===\n")
    print(result)
