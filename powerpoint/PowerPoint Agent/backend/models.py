"""
Pydantic models for the PowerPoint Alignment Agent.

These models define the data structures shared between:
- Frontend (TypeScript) and Backend (Python)
- Different agents (Scene Analyzer, Arranger)
"""

from enum import Enum
from pydantic import BaseModel, Field


class AlignmentType(str, Enum):
    """Available alignment operations."""
    HORIZONTAL_DISTRIBUTE = "horizontal_distribute"
    VERTICAL_DISTRIBUTE = "vertical_distribute"
    HORIZONTAL_CENTER = "horizontal_center"
    VERTICAL_CENTER = "vertical_center"


class VerticalPosition(str, Enum):
    """Vertical positioning for horizontal arrangements."""
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class HorizontalPosition(str, Enum):
    """Horizontal positioning for vertical arrangements."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Shape(BaseModel):
    """Basic shape information from PowerPoint."""
    id: str
    left: float
    top: float
    width: float
    height: float


class LabeledShape(BaseModel):
    """Shape with AI-generated label and description."""
    id: str
    label: str = Field(description="Short name, e.g., 'email icon', 'right arrow'")
    description: str = Field(description="Brief description including visual appearance")
    left: float
    top: float
    width: float
    height: float


# Scene Analysis (Step 1 of the flow)
class SceneAnalysisRequest(BaseModel):
    """Request to analyze a slide and label all shapes."""
    image_base64: str = Field(description="Base64 encoded PNG of the slide")
    shapes: list[Shape] = Field(description="All shapes on the slide with positions")


class SceneAnalysisResponse(BaseModel):
    """Response with labeled shapes."""
    labeled_shapes: list[LabeledShape]


# Arrangement (Step 2 of the flow)
class ArrangeRequest(BaseModel):
    """Request to arrange shapes based on user command."""
    user_message: str = Field(description="User's arrangement instruction")
    labeled_shapes: list[LabeledShape] = Field(description="Previously labeled shapes")


class ArrangeResponse(BaseModel):
    """Response with arrangement instructions."""
    order: list[str] = Field(description="Shape IDs in desired order")
    alignment: AlignmentType = Field(description="Alignment operation to apply")
    vertical_position: VerticalPosition = Field(
        default=VerticalPosition.MIDDLE,
        description="Vertical position for horizontal arrangements"
    )
    horizontal_position: HorizontalPosition = Field(
        default=HorizontalPosition.CENTER,
        description="Horizontal position for vertical arrangements"
    )
    explanation: str = Field(description="Human-readable explanation of the arrangement")


# Script Generation
class ScriptRequest(BaseModel):
    """Request to generate a presentation script for a slide."""
    image_base64: str = Field(description="Base64 encoded PNG of the slide")
    context: str = Field(default="", description="User's context: audience, purpose, notes, etc.")


class ScriptResponse(BaseModel):
    """Response with the generated script."""
    script: str = Field(description="The generated presentation script")
