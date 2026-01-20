"""Shared agent logic for all experts."""

from anthropic import Anthropic
from tools import TOOLS

client = Anthropic()


def run_agent(system_prompt: str, user_message: str, tool_results: list[dict] | None = None, conversation_history: list[dict] | None = None) -> dict:
    """
    Run a Claude agent with the given system prompt.

    Returns:
        {"response": "...", "conversation_history": [...]} if done
        {"tool_calls": [...], "conversation_history": [...]} if Claude wants tools
    """
    messages = conversation_history or []

    if not tool_results:
        messages.append({"role": "user", "content": user_message})
    else:
        tool_result_content = [
            {"type": "tool_result", "tool_use_id": r["tool_use_id"], "content": str(r["result"])}
            for r in tool_results
        ]
        messages.append({"role": "user", "content": tool_result_content})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        tools=TOOLS,
        messages=messages
    )

    # Parse response
    tool_calls = []
    text_response = ""
    assistant_content = []

    for block in response.content:
        if block.type == "tool_use":
            tool_calls.append({"id": block.id, "name": block.name, "args": block.input})
            assistant_content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
        elif block.type == "text":
            text_response += block.text
            assistant_content.append({"type": "text", "text": block.text})

    messages.append({"role": "assistant", "content": assistant_content})

    if tool_calls:
        return {"tool_calls": tool_calls, "conversation_history": messages}
    return {"response": text_response, "conversation_history": messages}
