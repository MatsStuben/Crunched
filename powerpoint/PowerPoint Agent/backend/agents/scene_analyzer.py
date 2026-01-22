"""
Scene Analyzer Agent.

Takes a slide screenshot and shape positions, uses Claude's vision
to identify and label each shape with a meaningful name and description.
"""

import logging
from anthropic import Anthropic

from models import Shape, LabeledShape

logger = logging.getLogger(__name__)
client = Anthropic()

LABEL_SHAPES_TOOL = {
    "name": "label_shapes",
    "description": "Label each shape identified in the slide",
    "input_schema": {
        "type": "object",
        "properties": {
            "labeled_shapes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "The shape ID (must match one from the input)"
                        },
                        "label": {
                            "type": "string",
                            "description": "Short descriptive name (e.g., 'email icon', 'right arrow', 'robot')"
                        },
                        "description": {
                            "type": "string",
                            "description": "Brief description of appearance and position"
                        }
                    },
                    "required": ["id", "label", "description"]
                }
            }
        },
        "required": ["labeled_shapes"]
    }
}

SYSTEM_PROMPT = """You are analyzing a PowerPoint slide to identify and label shapes.

You will receive:
1. An image of the slide
2. A list of shapes with their IDs and positions (left, top, width, height in points)

Your task:
- Match each shape position to what you see in the image
- Give each shape a short, meaningful label (e.g., "email icon", "right arrow", "robot", "spreadsheet")
- Provide a brief description of its appearance

Guidelines:
- Labels should be concise (1-3 words)
- Descriptions should mention visual appearance and relative position
- You MUST label ALL shapes provided in the input
- Use the exact shape IDs from the input

Always use the label_shapes tool to respond."""


def analyze_scene(image_base64: str, shapes: list[Shape]) -> list[LabeledShape]:
    """
    Analyze a slide screenshot and label all shapes.

    Args:
        image_base64: Base64 encoded PNG of the slide
        shapes: List of shapes with positions from PowerPoint

    Returns:
        List of LabeledShape with AI-generated labels and descriptions
    """
    logger.info(f"Analyzing scene with {len(shapes)} shapes")

    # Format shapes for the prompt
    shapes_description = "\n".join([
        f"- Shape ID: {s.id}, Position: left={s.left:.0f}, top={s.top:.0f}, "
        f"size: {s.width:.0f}x{s.height:.0f}"
        for s in shapes
    ])

    user_content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": image_base64
            }
        },
        {
            "type": "text",
            "text": f"Here are the shapes on this slide:\n\n{shapes_description}\n\nPlease label each shape."
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[LABEL_SHAPES_TOOL],
        tool_choice={"type": "tool", "name": "label_shapes"},
        messages=[{"role": "user", "content": user_content}]
    )

    tool_input = response.content[0].input
    logger.info(f"Scene analysis complete: {tool_input}")

    # Build LabeledShape objects by combining AI labels with original positions
    shapes_by_id = {s.id: s for s in shapes}
    labeled_shapes = []

    for item in tool_input["labeled_shapes"]:
        shape_id = item["id"]
        if shape_id in shapes_by_id:
            original = shapes_by_id[shape_id]
            labeled_shapes.append(LabeledShape(
                id=shape_id,
                label=item["label"],
                description=item["description"],
                left=original.left,
                top=original.top,
                width=original.width,
                height=original.height
            ))
        else:
            logger.warning(f"Shape ID {shape_id} from LLM not found in input shapes")

    # Warn if any shapes weren't labeled
    labeled_ids = {ls.id for ls in labeled_shapes}
    for shape in shapes:
        if shape.id not in labeled_ids:
            logger.warning(f"Shape {shape.id} was not labeled by the LLM")
            # Add with generic label
            labeled_shapes.append(LabeledShape(
                id=shape.id,
                label="unknown shape",
                description="Shape not identified",
                left=shape.left,
                top=shape.top,
                width=shape.width,
                height=shape.height
            ))

    return labeled_shapes
