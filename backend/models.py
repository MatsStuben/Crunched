"""Pydantic models for request/response."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    tool_results: list[dict] | None = None  # Results from frontend tool execution


class ToolCall(BaseModel):
    name: str
    args: dict


class ChatResponse(BaseModel):
    response: str | None = None  # Final response to display
    tool_calls: list[ToolCall] | None = None  # Tools for frontend to execute
