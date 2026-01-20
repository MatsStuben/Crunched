"""FastAPI backend for Crunched Excel add-in."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse, ToolCall
from agent import run_agent

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
    """Chat endpoint that uses Claude agent."""

    result = run_agent(
        user_message=request.message,
        tool_results=request.tool_results,
        conversation_history=request.conversation_history
    )

    if "tool_calls" in result:
        return ChatResponse(
            tool_calls=[
                ToolCall(id=tc["id"], name=tc["name"], args=tc["args"])
                for tc in result["tool_calls"]
            ],
            conversation_history=result["conversation_history"]
        )
    else:
        return ChatResponse(
            response=result["response"],
            conversation_history=result["conversation_history"]
        )


@app.get("/health")
async def health():
    return {"status": "ok"}