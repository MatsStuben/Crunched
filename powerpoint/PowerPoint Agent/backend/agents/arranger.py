"""
Arranger Agent.

Takes labeled shapes and a user command, determines the arrangement
order and alignment type to apply.
"""

import logging
from anthropic import Anthropic

from models import LabeledShape

logger = logging.getLogger(__name__)
client = Anthropic()

ARRANGE_TOOL = {
    "name": "arrange_shapes",
    "description": "Specify how to arrange the shapes based on the user's request",
    "input_schema": {
        "type": "object",
        "properties": {
            "order": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Shape IDs in the desired arrangement order (first = leftmost or topmost)"
            },
            "alignment": {
                "type": "string",
                "enum": ["horizontal_distribute", "vertical_distribute",
                         "horizontal_center", "vertical_center"],
                "description": "The alignment operation to apply"
            },
            "explanation": {
                "type": "string",
                "description": "Brief explanation of what will be done"
            }
        },
        "required": ["order", "alignment", "explanation"]
    }
}

SYSTEM_PROMPT = """You are arranging shapes on a PowerPoint slide based on user instructions.

You will receive:
1. A list of labeled shapes with their IDs, labels, and descriptions
2. The user's arrangement instruction

Your task:
- Determine which shapes to include in the arrangement
- Determine the order (which shape goes first, second, etc.)
- Choose the appropriate alignment type

Alignment types:
- horizontal_distribute: Spread shapes evenly LEFT-TO-RIGHT across the slide
  Use for: "arrange left to right", "in a row", "side by side", "from X to Y"

- vertical_distribute: Spread shapes evenly TOP-TO-BOTTOM across the slide
  Use for: "arrange top to bottom", "in a column", "stack vertically"

- horizontal_center: Align all shapes to the same VERTICAL center line (same X position)
  Use for: "center horizontally", "align centers", "stack centered"

- vertical_center: Align all shapes to the same HORIZONTAL center line (same Y position)
  Use for: "center vertically", "same height", "align on same row"

Guidelines:
- Match user's natural language to shape labels (e.g., "the email" → shape labeled "email interface")
- If user says "A then B then C", order should be [A_id, B_id, C_id]
- If user mentions "left to right" or describes a flow, use horizontal_distribute
- Only include shapes that the user mentions or implies
- If user says "all shapes", include everything
- IMPORTANT: Return the actual shape IDs, not the labels

Always use the arrange_shapes tool to respond."""


def arrange_shapes(user_message: str, labeled_shapes: list[LabeledShape]) -> dict:
    """
    Determine arrangement based on user command and labeled shapes.

    Args:
        user_message: User's natural language arrangement instruction
        labeled_shapes: Previously labeled shapes from scene analysis

    Returns:
        Dict with 'order' (list of shape IDs), 'alignment', and 'explanation'
    """
    logger.info(f"Arranging shapes. User message: '{user_message}'")
    logger.info(f"Available shapes: {[(s.id, s.label) for s in labeled_shapes]}")

    # Format shapes for the prompt - include ID explicitly
    shapes_description = "\n".join([
        f"- ID: \"{s.id}\" | Label: \"{s.label}\" | Description: {s.description}"
        for s in labeled_shapes
    ])

    user_content = f"""Available shapes on the slide:

{shapes_description}

User's instruction: "{user_message}"

Determine the arrangement. Return the shape IDs (not labels) in the order array."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        tools=[ARRANGE_TOOL],
        tool_choice={"type": "tool", "name": "arrange_shapes"},
        messages=[{"role": "user", "content": user_content}]
    )

    tool_input = response.content[0].input
    logger.info(f"Arrangement result: {tool_input}")

    # Validate that all returned IDs exist
    valid_ids = {s.id for s in labeled_shapes}
    filtered_order = [shape_id for shape_id in tool_input["order"] if shape_id in valid_ids]

    if len(filtered_order) != len(tool_input["order"]):
        invalid_ids = set(tool_input["order"]) - valid_ids
        logger.warning(f"Invalid shape IDs filtered out: {invalid_ids}")

    if len(filtered_order) == 0:
        logger.error("No valid shape IDs returned by arranger")
        raise ValueError("Could not match any shapes to the user's request")

    return {
        "order": filtered_order,
        "alignment": tool_input["alignment"],
        "explanation": tool_input["explanation"]
    }
