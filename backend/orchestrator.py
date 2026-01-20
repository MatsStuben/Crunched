"""Orchestrator - classifies tasks and gathers context in discrete steps."""

import logging
from anthropic import Anthropic

from models import ClassificationResult, DataStrategyResult

logger = logging.getLogger(__name__)
client = Anthropic()

CLASSIFY_PROMPT = """Classify the user's request using the classify_task tool.

Task types:
- bond_pricing: pricing bonds, bond valuation, bond DCF, calculating bond prices
- other: everything else"""

CLASSIFY_TOOL = {
    "name": "classify_task",
    "description": "Classify the user's request",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_type": {"type": "string", "enum": ["bond_pricing", "other"]},
            "needs_excel": {"type": "boolean", "description": "Whether this task needs Excel data"},
            "reasoning": {"type": "string", "description": "Brief explanation"}
        },
        "required": ["task_type", "needs_excel", "reasoning"]
    }
}

DATA_STRATEGY_PROMPT = """Decide how to gather Excel data using the data_strategy tool.

Rules:
- read_all: if total data is small (< 100 rows), specify ranges to read
- ask_user: if data is large, ask user to specify the relevant range
- skip: if no relevant data exists"""

DATA_STRATEGY_TOOL = {
    "name": "data_strategy",
    "description": "Decide how to gather Excel data for the task",
    "input_schema": {
        "type": "object",
        "properties": {
            "strategy": {"type": "string", "enum": ["read_all", "ask_user", "skip"]},
            "ranges_to_read": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Excel ranges to read, e.g. ['Sheet1!A1:B20']"
            },
            "question_for_user": {
                "type": ["string", "null"],
                "description": "Question to ask if strategy is ask_user"
            }
        },
        "required": ["strategy", "ranges_to_read", "question_for_user"]
    }
}


def step1_classify(user_message: str) -> ClassificationResult:
    """Classify the task type and determine if Excel data is needed."""
    logger.info("[ORCHESTRATOR] step1_classify called")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system=CLASSIFY_PROMPT,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_task"},
        messages=[{"role": "user", "content": user_message}]
    )

    # Tool use guarantees structured output
    tool_input = response.content[0].input
    logger.info(f"[ORCHESTRATOR] Classification: {tool_input}")
    return ClassificationResult(**tool_input)


def step3_data_strategy(workbook_info: dict, user_message: str) -> DataStrategyResult:
    """Based on workbook info, decide how to gather data."""
    logger.info("[ORCHESTRATOR] step3_data_strategy called")

    sheets_summary = [f"- {s['name']}: {s['usedRange']}" for s in workbook_info.get("sheets", [])]
    sheets_text = "\n".join(sheets_summary) or "No sheets found"
    user_content = f"User request: {user_message}\n\nWorkbook structure:\n{sheets_text}"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        system=DATA_STRATEGY_PROMPT,
        tools=[DATA_STRATEGY_TOOL],
        tool_choice={"type": "tool", "name": "data_strategy"},
        messages=[{"role": "user", "content": user_content}]
    )

    tool_input = response.content[0].input
    logger.info(f"[ORCHESTRATOR] Data strategy: {tool_input}")
    return DataStrategyResult(**tool_input)