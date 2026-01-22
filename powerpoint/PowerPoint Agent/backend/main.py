"""
Simple PowerPoint alignment agent backend.
Uses LLM to understand alignment requests and returns alignment instructions.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from anthropic import Anthropic

from models import (
    SceneAnalysisRequest, SceneAnalysisResponse, Shape,
    ArrangeRequest, ArrangeResponse, LabeledShape
)
from agents.scene_analyzer import analyze_scene
from agents.arranger import arrange_shapes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Session storage: {session_id: {"labeled_shapes": [...]}}
sessions: dict[str, dict] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Anthropic()

class AlignRequest(BaseModel):
    message: str
    shape_count: int = 0

class AlignResponse(BaseModel):
    alignment_type: str  # "horizontal_center", "vertical_center", "horizontal_distribute", "vertical_distribute"
    explanation: str

ALIGNMENT_TOOL = {
    "name": "align_shapes",
    "description": "Specify how to align the selected shapes",
    "input_schema": {
        "type": "object",
        "properties": {
            "alignment_type": {
                "type": "string",
                "enum": ["horizontal_center", "vertical_center", "horizontal_distribute", "vertical_distribute"],
                "description": "horizontal_center: align all shapes to same vertical center (same Y). vertical_center: align to same horizontal center (same X). horizontal_distribute: spread evenly left-to-right. vertical_distribute: spread evenly top-to-bottom."
            },
            "explanation": {
                "type": "string",
                "description": "Brief explanation of what alignment will be applied"
            }
        },
        "required": ["alignment_type", "explanation"]
    }
}

SYSTEM_PROMPT = """You are a PowerPoint alignment assistant. The user wants to align shapes in their presentation.

Based on their request, determine the best alignment type:
- horizontal_center: Align all shapes so they have the same vertical position (Y coordinate) - use for "align horizontally", "same height", "in a row"
- vertical_center: Align all shapes so they have the same horizontal position (X coordinate) - use for "align vertically", "stack", "in a column"
- horizontal_distribute: Spread shapes evenly from left to right - use for "distribute", "space evenly", "equal spacing horizontally"
- vertical_distribute: Spread shapes evenly from top to bottom - use for "distribute vertically", "space evenly vertically"

If the request is ambiguous, default to horizontal_center as it's the most common alignment.
Always use the align_shapes tool to respond."""

@app.post("/align")
async def align(request: AlignRequest) -> AlignResponse:
    logger.info(f"Received alignment request: message='{request.message}', shape_count={request.shape_count}")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            tools=[ALIGNMENT_TOOL],
            tool_choice={"type": "tool", "name": "align_shapes"},
            messages=[{"role": "user", "content": f"User request: {request.message}\nNumber of shapes selected: {request.shape_count}"}]
        )

        tool_input = response.content[0].input
        logger.info(f"LLM response: alignment_type={tool_input['alignment_type']}, explanation={tool_input['explanation']}")

        return AlignResponse(
            alignment_type=tool_input["alignment_type"],
            explanation=tool_input["explanation"]
        )
    except Exception as e:
        logger.error(f"Error processing alignment request: {e}")
        raise

class DescribeRequest(BaseModel):
    image_base64: str

class DescribeResponse(BaseModel):
    description: str

@app.post("/describe")
async def describe_slide(request: DescribeRequest) -> DescribeResponse:
    """Send slide screenshot to Claude and get a description."""
    logger.info(f"Received describe request, image length: {len(request.image_base64)}")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": request.image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Describe what you see in this PowerPoint slide. List each distinct object/shape you can identify and its approximate position (left, center, right, top, bottom)."
                    }
                ]
            }]
        )

        description = response.content[0].text
        logger.info(f"Claude description: {description[:200]}...")

        return DescribeResponse(description=description)
    except Exception as e:
        logger.error(f"Error describing slide: {e}")
        raise

@app.post("/analyze")
async def analyze(request: SceneAnalysisRequest) -> SceneAnalysisResponse:
    """Analyze slide screenshot and label all shapes."""
    logger.info(f"Received analyze request with {len(request.shapes)} shapes")

    try:
        labeled_shapes = analyze_scene(
            image_base64=request.image_base64,
            shapes=request.shapes
        )
        logger.info(f"Analysis complete: {[s.label for s in labeled_shapes]}")
        return SceneAnalysisResponse(labeled_shapes=labeled_shapes)
    except Exception as e:
        logger.error(f"Error analyzing scene: {e}")
        raise

class StartRequest(BaseModel):
    session_id: str
    image_base64: str
    shapes: list[Shape]

class StartResponse(BaseModel):
    session_id: str
    labeled_shapes: list[LabeledShape]

@app.post("/start")
async def start_session(request: StartRequest) -> StartResponse:
    """
    Initialize a session by analyzing the slide.
    Called when user opens the chat / clicks Start.
    """
    logger.info(f"Starting session {request.session_id} with {len(request.shapes)} shapes")

    try:
        # Analyze the scene
        labeled_shapes = analyze_scene(
            image_base64=request.image_base64,
            shapes=request.shapes
        )

        # Store in session
        sessions[request.session_id] = {
            "labeled_shapes": labeled_shapes
        }

        logger.info(f"Session {request.session_id} initialized with shapes: {[s.label for s in labeled_shapes]}")

        return StartResponse(
            session_id=request.session_id,
            labeled_shapes=labeled_shapes
        )
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise


@app.post("/arrange")
async def arrange(request: ArrangeRequest) -> ArrangeResponse:
    """
    Arrange shapes based on user command.
    Uses labeled shapes from session or from request.
    """
    logger.info(f"Arrange request: '{request.user_message}'")

    # Use shapes from request (frontend sends stored shapes)
    if not request.labeled_shapes:
        raise ValueError("No labeled shapes provided")

    try:
        result = arrange_shapes(
            user_message=request.user_message,
            labeled_shapes=request.labeled_shapes
        )

        return ArrangeResponse(
            order=result["order"],
            alignment=result["alignment"],
            explanation=result["explanation"]
        )
    except Exception as e:
        logger.error(f"Error arranging shapes: {e}")
        raise


@app.get("/health")
async def health():
    return {"status": "ok"}
