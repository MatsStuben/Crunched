"""Pydantic models for request/response."""

from pydantic import BaseModel


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
