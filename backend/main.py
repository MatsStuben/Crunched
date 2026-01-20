"""FastAPI backend for Crunched Excel add-in."""

import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse, ToolCall
from agent import run_agent

app = FastAPI()

# Session storage (in production, use Redis)
sessions: dict[str, list[dict]] = {}

# Allow requests from the Excel add-in (localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat endpoint with session management."""

    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    conversation_history = sessions.get(session_id, [])

    # Run agent
    result = run_agent(
        user_message=request.message,
        tool_results=request.tool_results,
        conversation_history=conversation_history
    )

    # Save updated history
    sessions[session_id] = result["conversation_history"]

    # Return response (without history)
    if "tool_calls" in result:
        return ChatResponse(
            session_id=session_id,
            tool_calls=[
                ToolCall(id=tc["id"], name=tc["name"], args=tc["args"])
                for tc in result["tool_calls"]
            ]
        )
    else:
        return ChatResponse(
            session_id=session_id,
            response=result["response"]
        )


@app.get("/health")
async def health():
    return {"status": "ok"}
