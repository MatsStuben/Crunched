"""Claude agent for Excel operations."""

from anthropic import Anthropic
from tools import TOOLS

client = Anthropic()  # Uses ANTHROPIC_API_KEY from environment

SYSTEM_PROMPT = """You are an Excel assistant that helps users read and write data in their spreadsheet.

You have access to tools to read and write Excel cells. Use them when the user asks about cell contents or wants to modify the spreadsheet.

IMPORTANT: When writing calculations, ALWAYS write Excel formulas (e.g., "=SUM(A1:A10)"), NOT computed values. This keeps the spreadsheet dynamic — when inputs change, results update automatically. Never calculate values yourself and write the result; always write the formula that Excel will evaluate.

Keep responses concise."""


def run_agent(user_message: str, tool_results: list[dict] | None = None, conversation_history: list[dict] | None = None):
    """
    Run the Claude agent.

    Returns:
        dict with either:
        - {"response": "final text"} if done
        - {"tool_calls": [...]} if Claude wants to use tools
    """
    messages = conversation_history or []

    # Add user message if this is a new conversation
    if not tool_results:
        messages.append({"role": "user", "content": user_message})
    else:
        # Add tool results to continue the conversation
        tool_result_content = []
        for result in tool_results:
            tool_result_content.append({
                "type": "tool_result",
                "tool_use_id": result["tool_use_id"],
                "content": str(result["result"])
            })
        messages.append({"role": "user", "content": tool_result_content})

    # Call Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=messages
    )

    # Check if Claude wants to use tools
    tool_calls = []
    text_response = ""

    for block in response.content:
        if block.type == "tool_use":
            tool_calls.append({
                "id": block.id,
                "name": block.name,
                "args": block.input
            })
        elif block.type == "text":
            text_response += block.text

    # Add assistant response to history (convert to serializable format)
    assistant_content = []
    for block in response.content:
        if block.type == "tool_use":
            assistant_content.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input
            })
        elif block.type == "text":
            assistant_content.append({
                "type": "text",
                "text": block.text
            })
    messages.append({"role": "assistant", "content": assistant_content})

    if tool_calls:
        return {
            "tool_calls": tool_calls,
            "conversation_history": messages
        }
    else:
        return {
            "response": text_response,
            "conversation_history": messages
        }
