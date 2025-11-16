import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams


async def _run_web_summary_agent(article_url: str) -> str:
    """
    Internal async function that launches an MCP browser,
    loads the URL, extracts content, and summarises it.
    """

    model_client = OpenAIChatCompletionClient(model="gpt-4.1")

    server_params = StdioServerParams(
        command="npx",
        args=["@playwright/mcp@latest", "--headless"],
    )

    async with McpWorkbench(server_params) as mcp:
        agent = AssistantAgent(
            "forest_research_assistant",
            model_client=model_client,
            workbench=mcp,
            model_client_stream=False,
            max_tool_iterations=10,
        )

        task = (
            f"Load this URL: {article_url}. "
            "Extract all the readable article text. "
            "Summarize it into 4–7 key bullet points focusing on forest "
            "conservation actions, policy recommendations, environmental "
            "impact measures, and any Kenya/Makueni-relevant insights."
        )

        result = await agent.run(task=task)
        return result.final_answer


def run_web_summary(article_url: str) -> str:
    """
    Public function that Flask can import & call synchronously.
    """

    return asyncio.run(_run_web_summary_agent(article_url))
