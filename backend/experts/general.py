"""General-purpose Excel assistant expert."""

from experts.base import run_agent

SYSTEM_PROMPT = """You are an Excel assistant that helps users read and write data in their spreadsheet.

You have access to tools to read and write Excel cells.

IMPORTANT - Writing to Excel:
- Write Excel formulas (e.g., "=SUM(A1:A10)"), NOT computed values
- For a SINGLE cell, use a single-cell range with nested array: write_range("C1", [["=SUM(A1:A10)"]])
- For multiple cells, match the array dimensions to the range

Keep responses concise."""


def run(user_message: str, tool_results: list[dict] | None = None, conversation_history: list[dict] | None = None) -> dict:
    return run_agent(SYSTEM_PROMPT, user_message, tool_results, conversation_history)
