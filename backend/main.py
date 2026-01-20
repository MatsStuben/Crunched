"""Minimal FastAPI backend for testing."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse, ToolCall

app = FastAPI()

# Allow requests from the Excel add-in (localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Simple test endpoint - returns a tool call first, then a response."""

    # If we received tool results, return final response
    if request.tool_results:
        tool_data = request.tool_results[0]
        return ChatResponse(
            response=f"Got data from Excel: {tool_data.get('result', 'no result')}"
        )

    # First call: ask frontend to read a cell
    if "read" in request.message.lower():
        return ChatResponse(
            tool_calls=[ToolCall(name="read_range", args={"range": "A1:B2"})]
        )

    # Default: just echo back
    return ChatResponse(response=f"Echo: {request.message}")


@app.get("/health")
async def health():
    return {"status": "ok"}
