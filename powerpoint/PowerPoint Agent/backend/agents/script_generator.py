"""
Script Generator Agent.

Takes a slide screenshot and user context, generates a presentation script.
"""

import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)
client = Anthropic()

SYSTEM_PROMPT = """You are a professional presentation coach helping create engaging scripts for PowerPoint slides.

Given a slide image and context from the presenter, write a natural, conversational script they can use when presenting this slide.

Guidelines:
- Write in first person as if the presenter is speaking
- Keep it conversational and engaging, not robotic
- Include natural transitions and emphasis points
- Adapt tone based on the context provided (formal presentation, casual team meeting, etc.)
- Reference specific elements visible on the slide
- Suggest where to pause, emphasize, or gesture if appropriate
- Keep the script concise but complete - typically 30-90 seconds of speaking time per slide
- If the context mentions the audience or purpose, tailor the script accordingly

Output the script directly without any preamble or explanation."""


def generate_script(image_base64: str, context: str) -> str:
    """
    Generate a presentation script for a slide.

    Args:
        image_base64: Base64 encoded PNG of the slide
        context: User's context about the presentation (audience, purpose, notes, etc.)

    Returns:
        The generated script as a string
    """
    logger.info(f"Generating script. Context length: {len(context)} chars")

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
            "text": f"""Please write a presentation script for this slide.

Context from the presenter:
{context if context else "No additional context provided."}

Write the script the presenter should say when showing this slide."""
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}]
    )

    script = response.content[0].text
    logger.info(f"Generated script: {len(script)} chars")

    return script
