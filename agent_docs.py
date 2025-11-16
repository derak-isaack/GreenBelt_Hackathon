# run_agent_with_docs.py
import asyncio
import os
from textwrap import shorten

from analyis import df  
from pypdf import PdfReader

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams

MAX_CONTEXT_CHARS = 50_000  
PDF_CHUNK_SNIPPET = 10_000  


def extract_pdf_text(path: str) -> str:
    """Extract text from a PDF using pypdf (works for many PDFs)."""
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
    """Create a summarized context string from CSV df and PDF texts.
       pdf_paths: dict mapping friendly_name -> path
    """
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

    # PDFs
    for name, path in pdf_paths.items():
        try:
            txt = extract_pdf_text(path)
            snippet = shorten(txt, width=PDF_CHUNK_SNIPPET, placeholder=" ...[truncated]...")
            parts.append(f"=== PDF: {name} ({os.path.basename(path)}) ===")
            parts.append(snippet)
        except FileNotFoundError:
            parts.append(f"=== PDF: {name} ({path}) ===\n<FILE NOT FOUND>")
        except Exception as e:
            parts.append(f"=== PDF: {name} ({path}) ===\n<ERROR extracting PDF: {e}>")

    combined = "\n\n".join(parts)
    if len(combined) > MAX_CONTEXT_CHARS:
        combined = combined[: MAX_CONTEXT_CHARS - 200] + "\n\n...[OVERALL CONTEXT TRUNCATED]..."
    return combined


async def policy_evaluation() -> None:
    model_client = OpenAIChatCompletionClient(model="gpt-5.1")  

    server_params = StdioServerParams(
        command="npx",
        args=[
            "@playwright/mcp@latest",
            "--headless",
        ],
    )

    
    pdfs = {
        "Makueni County Bill": "makueniBill.pdf",
        "FOLAREP": "Makueni-FOLAREP.pdf",
    }

    data_context = build_combined_context(df, pdfs)

    task_text = (
    "You are a policy effectiveness evaluator. Using the CSV data containing monthly "
    "biomass and forest cover measurements derived from satellite data, and the two PDF "
    "documents (Makueni County Bill and FOLAREP), perform the following:\n\n"
    "1. Extract all mitigation steps, policies, or proposed actions from the PDFs.\n"
    "2. Examine the biomass/forest cover trends in the CSV over months.\n"
    "3. For each proposed step, determine whether the observed data indicates it is achieving "
    "its intended outcome (e.g., increased biomass or forest cover).\n"
    "4. Highlight any correlation between proposed actions and observed improvements. "
    "If data is missing or inconclusive, clearly note that.\n"
    "5. Present results in a structured way (table or bullet points) showing:\n"
    "   - Proposed Step\n"
    "   - Evidence from PDFs / CSV\n"
    "   - Observed Outcome\n"
    "   - Effectiveness Assessment\n\n"
    "This analysis will guide derivation of additional vegetation indices for monitoring forest cover.\n\n"
    f"=== DATA CONTEXT (CSV + PDF snippets) ===\n{data_context}"
)


    async with McpWorkbench(server_params) as mcp:
        agent = AssistantAgent(
            "web_browsing_assistant",
            model_client=model_client,
            workbench=mcp,
            model_client_stream=True,
            max_tool_iterations=10,
        )

        # await Console(agent.run_stream(task=task_text)).start()
        result = await agent.run(task=task_text)
        return result.messages[-1].content if result.messages else ""

