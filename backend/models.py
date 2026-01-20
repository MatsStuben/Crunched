"""Pydantic models for request/response."""

from enum import Enum
from pydantic import BaseModel, field_validator


# --- Orchestrator Models ---

class TaskType(str, Enum):
    BOND_PRICING = "bond_pricing"
    OTHER = "other"


class DataStrategy(str, Enum):
    READ_ALL = "read_all"
    ASK_USER = "ask_user"
    SKIP = "skip"


class ClassificationResult(BaseModel):
    """Result from step1_classify."""
    task_type: TaskType
    needs_excel: bool
    reasoning: str

    @field_validator("task_type", mode="before")
    @classmethod
    def normalize(cls, v):
        return v.lower().strip() if isinstance(v, str) else v


class DataStrategyResult(BaseModel):
    """Result from step3_data_strategy."""
    strategy: DataStrategy
    ranges_to_read: list[str] = []
    question_for_user: str | None = None

    @field_validator("strategy", mode="before")
    @classmethod
    def normalize(cls, v):
        return v.lower().strip() if isinstance(v, str) else v


# --- API Models ---

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # None = new session
    tool_results: list[dict] | None = None


class ToolCall(BaseModel):
    id: str
    name: str
    args: dict


class ChatResponse(BaseModel):
    session_id: str  # Always returned so frontend can continue session
    response: str | None = None
    tool_calls: list[ToolCall] | None = None
