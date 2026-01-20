"""Pydantic models for request/response."""

from typing import Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    tool_results: list[dict] | None = None  # Results from frontend tool execution
    conversation_history: list[dict] | None = None  # For multi-turn conversations


class ToolCall(BaseModel):
    id: str  # Claude's tool_use_id - needed to match results
    name: str
    args: dict


class ChatResponse(BaseModel):
    response: str | None = None  # Final response to display
    tool_calls: list[ToolCall] | None = None  # Tools for frontend to execute
    conversation_history: list[Any] | None = None  # Pass back for next request