"""Orchestrator - classifies tasks and gathers context in discrete steps."""

import json
import logging
from anthropic import Anthropic
from pydantic import ValidationError

from models import ClassificationResult, DataStrategyResult

logger = logging.getLogger(__name__)
client = Anthropic()

MAX_RETRIES = 2

CLASSIFY_PROMPT = """Classify the user's request. Return JSON only:

{"task_type": "bond_pricing" | "other", "needs_excel": true | false, "reasoning": "..."}

Task types:
- bond_pricing: pricing bonds, bond valuation, bond DCF, calculating bond prices
- other: everything else"""

DATA_STRATEGY_PROMPT = """Decide how to gather Excel data. Return JSON only:

{"strategy": "read_all" | "ask_user" | "skip", "ranges_to_read": ["Sheet1!A1:D20"] | [], "question_for_user": "..." | null}

Rules:
- read_all: if total data is small (< 100 rows), specify ranges to read
- ask_user: if data is large, ask user to specify the relevant range
- skip: if no relevant data exists"""


def _extract_json(text: str) -> str:
    """Extract JSON from response, handling markdown code blocks anywhere in text."""
    text = text.strip()

    # Find JSON code block anywhere in text
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    # Try finding generic code block
    if "```" in text:
        start = text.find("```") + 3
        # Skip language identifier if on same line
        newline = text.find("\n", start)
        if newline != -1:
            start = newline + 1
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    return text


def _call_with_retry(system: str, user_content: str, model_class: type, default: dict) -> object:
    """Call Claude and validate response with Pydantic, retrying on failure."""
    messages = [{"role": "user", "content": user_content}]

    for attempt in range(MAX_RETRIES + 1):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=system,
            messages=messages
        )

        text = response.content[0].text
        logger.info(f"[ORCHESTRATOR] Response (attempt {attempt + 1}): {text}")

        try:
            json_str = _extract_json(text)
            parsed = json.loads(json_str)
            result = model_class(**parsed)
            logger.info(f"[ORCHESTRATOR] Validated: {result}")
            return result
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"[ORCHESTRATOR] Validation failed (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES:
                messages = [
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": f"Invalid JSON: {e}. Return valid JSON only."}
                ]

    logger.error("[ORCHESTRATOR] Failed after retries, using defaults")
    return model_class(**default)


def step1_classify(user_message: str) -> ClassificationResult:
    """Classify the task type and determine if Excel data is needed."""
    logger.info("[ORCHESTRATOR] step1_classify called")
    return _call_with_retry(
        system=CLASSIFY_PROMPT,
        user_content=user_message,
        model_class=ClassificationResult,
        default={"task_type": "other", "needs_excel": False, "reasoning": "Classification failed"}
    )


def step3_data_strategy(workbook_info: dict, user_message: str) -> DataStrategyResult:
    """Based on workbook info, decide how to gather data."""
    logger.info("[ORCHESTRATOR] step3_data_strategy called")

    sheets_summary = [f"- {s['name']}: {s['usedRange']}" for s in workbook_info.get("sheets", [])]
    sheets_text = "\n".join(sheets_summary) or "No sheets found"
    user_content = f"User request: {user_message}\n\nWorkbook structure:\n{sheets_text}"

    return _call_with_retry(
        system=DATA_STRATEGY_PROMPT,
        user_content=user_content,
        model_class=DataStrategyResult,
        default={"strategy": "skip", "ranges_to_read": [], "question_for_user": None}
    )