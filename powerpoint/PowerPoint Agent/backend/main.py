"""
PowerPoint Alignment Agent Backend.

Uses vision-powered LLM to identify shapes and arrange them based on natural language commands.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import (
    SceneAnalysisRequest, SceneAnalysisResponse, Shape,
    ArrangeRequest, ArrangeResponse, LabeledShape,
    ScriptRequest, ScriptResponse
)
from agents.scene_analyzer import analyze_scene
from agents.arranger import arrange_shapes
from agents.script_generator import generate_script

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
        labeled_shapes = analyze_scene(
            image_base64=request.image_base64,
            shapes=request.shapes
        )

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
    """
    logger.info(f"Arrange request: '{request.user_message}'")

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
            vertical_position=result["vertical_position"],
            horizontal_position=result["horizontal_position"],
            explanation=result["explanation"]
        )
    except Exception as e:
        logger.error(f"Error arranging shapes: {e}")
        raise


@app.post("/generate-script")
async def generate_script_endpoint(request: ScriptRequest) -> ScriptResponse:
    """
    Generate a presentation script for a slide.
    """
    logger.info(f"Script generation request. Context length: {len(request.context)} chars")

    try:
        script = generate_script(
            image_base64=request.image_base64,
            context=request.context
        )
        return ScriptResponse(script=script)
    except Exception as e:
        logger.error(f"Error generating script: {e}")
        raise


@app.get("/health")
async def health():
    return {"status": "ok"}
