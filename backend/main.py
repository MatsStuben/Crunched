"""FastAPI backend for Crunched Excel add-in."""

import uuid
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse, ToolCall, DataStrategy, TaskType
from orchestrator import step1_classify, step3_data_strategy
from experts import run_general, run_bond_pricing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Session storage: {session_id: {phase, original_message, classification, workbook_info, excel_context, conversation_history}}
sessions: dict[str, dict] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat endpoint with orchestrated flow."""

    session_id = request.session_id or str(uuid.uuid4())

    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = {
            "phase": "classify",
            "original_message": request.message,
            "classification": None,
            "workbook_info": None,
            "data_strategy": None,
            "excel_context": None,
            "conversation_history": []
        }

    session = sessions[session_id]

    # Phase: CLASSIFY
    if session["phase"] == "classify":
        logger.info(f"[CLASSIFY] Message: {request.message}")
        classification = step1_classify(request.message)
        session["classification"] = classification
        logger.info(f"[CLASSIFY] Result: {classification}")

        if classification.needs_excel:
            session["phase"] = "get_workbook"
            # Return tool call to get workbook info
            return ChatResponse(
                session_id=session_id,
                tool_calls=[ToolCall(id="orch_wb_info", name="get_workbook_info", args={})]
            )
        else:
            # Skip to expert
            session["phase"] = "expert"
            return await run_expert_phase(session_id, session, request)

    # Phase: GET_WORKBOOK (received workbook info from frontend)
    if session["phase"] == "get_workbook":
        logger.info(f"[GET_WORKBOOK] Received tool_results: {request.tool_results}")
        if request.tool_results:
            session["workbook_info"] = request.tool_results[0].get("result", {})
        logger.info(f"[GET_WORKBOOK] Workbook info: {session['workbook_info']}")

        # Now decide data strategy
        data_strategy = step3_data_strategy(session["workbook_info"], session["original_message"])
        session["data_strategy"] = data_strategy
        logger.info(f"[DATA_STRATEGY] Result: {data_strategy}")

        if data_strategy.strategy == DataStrategy.READ_ALL and data_strategy.ranges_to_read:
            session["phase"] = "read_data"
            # Return tool calls to read the ranges
            tool_calls = [
                ToolCall(id=f"orch_read_{i}", name="read_range", args={"range": r})
                for i, r in enumerate(data_strategy.ranges_to_read)
            ]
            return ChatResponse(session_id=session_id, tool_calls=tool_calls)

        elif data_strategy.strategy == DataStrategy.ASK_USER:
            session["phase"] = "waiting_for_user"
            return ChatResponse(
                session_id=session_id,
                response=data_strategy.question_for_user or "Which part of the spreadsheet contains the relevant data?"
            )

        else:  # skip
            session["phase"] = "expert"
            return await run_expert_phase(session_id, session, request)

    # Phase: READ_DATA (received Excel data from frontend)
    if session["phase"] == "read_data":
        if request.tool_results:
            # Combine all read results into context
            excel_context = []
            for result in request.tool_results:
                excel_context.append(result.get("result", []))
            session["excel_context"] = excel_context

        session["phase"] = "expert"
        return await run_expert_phase(session_id, session, request)

    # Phase: WAITING_FOR_USER (user provided more info)
    if session["phase"] == "waiting_for_user":
        # User has responded with more specific info
        # Re-run data strategy with user's input or go back to get_workbook
        session["original_message"] = f"{session['original_message']}\n\nUser clarification: {request.message}"
        session["phase"] = "get_workbook"
        return ChatResponse(
            session_id=session_id,
            tool_calls=[ToolCall(id="orch_wb_info_2", name="get_workbook_info", args={})]
        )

    # Phase: EXPERT
    if session["phase"] == "expert":
        return await run_expert_phase(session_id, session, request)

    # Fallback
    return ChatResponse(session_id=session_id, response="Something went wrong.")


async def run_expert_phase(session_id: str, session: dict, request: ChatRequest) -> ChatResponse:
    """Run the expert agent with gathered context."""
    task_type = session["classification"].task_type if session["classification"] else TaskType.OTHER
    logger.info(f"[EXPERT] Starting expert phase with task_type={task_type}")

    # Build context for the expert
    context_parts = [session["original_message"]]
    if session["excel_context"]:
        context_parts.append(f"\n\nExcel data found:\n{session['excel_context']}")
    full_context = "".join(context_parts)
    logger.info(f"[EXPERT] Full context: {full_context[:500]}...")

    # Route to correct expert
    expert_fn = run_bond_pricing if task_type == TaskType.BOND_PRICING else run_general

    result = expert_fn(
        user_message=full_context,
        tool_results=request.tool_results if session.get("expert_started") else None,
        conversation_history=session["conversation_history"]
    )

    session["expert_started"] = True
    session["conversation_history"] = result["conversation_history"]

    if "tool_calls" in result:
        return ChatResponse(
            session_id=session_id,
            tool_calls=[
                ToolCall(id=tc["id"], name=tc["name"], args=tc["args"])
                for tc in result["tool_calls"]
            ]
        )
    else:
        # Reset session for next conversation
        del sessions[session_id]
        return ChatResponse(session_id=session_id, response=result["response"])


@app.get("/health")
async def health():
    return {"status": "ok"}