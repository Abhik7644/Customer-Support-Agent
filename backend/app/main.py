from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
import json
from fastapi.responses import StreamingResponse

from backend.app.auth import register_customer, authenticate_customer, create_access_token
from backend.app.dependencies import get_current_customer_id
from backend.app.database import run_query , run_write
from backend.app.agent_v2 import builder, Command
from backend.app.dependencies import get_current_admin_id
from backend.app.tools.rag_tools import get_vector_store

from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from backend.app.agent_v2 import builder
from backend.app.config import settings
from psycopg.rows import dict_row

DB_URI = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncConnectionPool(
        conninfo=DB_URI,
        max_size=10,
        kwargs={"autocommit": True, "row_factory": dict_row},
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()  # creates the checkpoint tables if they don't exist yet - safe to call every startup
        app.state.graph = builder.compile(checkpointer=checkpointer)
        yield
    # pool closes automatically on shutdown


app = FastAPI(title="Customer Support Agent API", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Auth ----------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/auth/register", response_model=TokenResponse)
def register(request: RegisterRequest):
    try:
        customer_id = register_customer(request.name, request.email, request.password)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not register - email may already be in use.")
    return TokenResponse(access_token=create_access_token(customer_id))


@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest):
    customer_id = authenticate_customer(request.email, request.password)
    if customer_id is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return TokenResponse(access_token=create_access_token(customer_id))


# ---------- Chat ----------

class ChatRequest(BaseModel):
    message: str


class ApprovalRequest(BaseModel):
    approved: bool


def _build_config(customer_id: int) -> RunnableConfig:
    return {
        "configurable": {
            "thread_id": f"customer-{customer_id}",
            "current_customer_id": customer_id,
        }
    }

from fastapi import Request

@app.post("/chat")
async def chat(request: Request, chat_request: ChatRequest, customer_id: int = Depends(get_current_customer_id)):
    graph = request.app.state.graph
    config = _build_config(customer_id)
    result = await graph.ainvoke({"messages": [HumanMessage(content=chat_request.message)]}, config=config)

    if "__interrupt__" in result:
        interrupt_data = result["__interrupt__"][0].value
        return {"status": "approval_required", "details": interrupt_data}

    return {"status": "ok", "reply": result["messages"][-1].content}


@app.post("/chat/approve")
async def approve_pending_action(request: Request, approval_request: ApprovalRequest, customer_id: int = Depends(get_current_customer_id)):
    graph = request.app.state.graph
    config = _build_config(customer_id)
    result = await graph.ainvoke(Command(resume={"approved": approval_request.approved}), config=config)
    return {"status": "ok", "reply": result["messages"][-1].content}


@app.get("/chat/history")
async def get_chat_history(request: Request, customer_id: int = Depends(get_current_customer_id)):
    graph = request.app.state.graph
    config = _build_config(customer_id)
    state = await graph.aget_state(config)
    messages = state.values.get("messages", []) if state.values else []

    history = []
    for m in messages:
        if isinstance(m, HumanMessage):
            history.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage) and m.content:
            history.append({"role": "assistant", "content": m.content})
    return history


@app.post("/chat/stream")
async def chat_stream(request: Request, chat_request: ChatRequest, customer_id: int = Depends(get_current_customer_id)):
    graph = request.app.state.graph
    config = _build_config(customer_id)

    async def event_generator():
        async for mode, chunk in graph.astream(
            {"messages": [HumanMessage(content=chat_request.message)]},
            config=config,
            stream_mode=["updates", "messages"],
        ):
            if mode == "messages" and isinstance(chunk, tuple):
                message_chunk, metadata = chunk
                if (
                    metadata.get("langgraph_node") == "agent"
                    and getattr(message_chunk, "content", None)
                    and not getattr(message_chunk, "tool_call_chunks", None)
                ):
                    yield f"data: {json.dumps({'type': 'token', 'content': message_chunk.content})}\n\n"
            elif mode == "updates" and isinstance(chunk, dict):
                if "__interrupt__" in chunk:
                    interrupt_data = chunk["__interrupt__"][0].value
                    yield f"data: {json.dumps({'type': 'interrupt', 'details': interrupt_data})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/chat/approve/stream")
async def approve_stream(request: Request, approval_request: ApprovalRequest, customer_id: int = Depends(get_current_customer_id)):
    graph = request.app.state.graph
    config = _build_config(customer_id)

    async def event_generator():
        async for mode, chunk in graph.astream(
            Command(resume={"approved": approval_request.approved}),
            config=config,
            stream_mode=["updates", "messages"],
        ):
            if mode == "messages" and isinstance(chunk, tuple):
                message_chunk, metadata = chunk
                if (
                    metadata.get("langgraph_node") == "agent"
                    and getattr(message_chunk, "content", None)
                    and not getattr(message_chunk, "tool_call_chunks", None)
                ):
                    yield f"data: {json.dumps({'type': 'token', 'content': message_chunk.content})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")



@app.get("/admin/faq-gaps")
def list_faq_gaps(admin_id: int = Depends(get_current_admin_id)):
    return run_query(
        "SELECT * FROM faq_gaps WHERE status = 'pending' ORDER BY created_at DESC;"
    )


class ResolveGapRequest(BaseModel):
    answer: str


@app.post("/admin/faq-gaps/{gap_id}/resolve")
def resolve_faq_gap(gap_id: int, request: ResolveGapRequest, admin_id: int = Depends(get_current_admin_id)):
    rows = run_query("SELECT question FROM faq_gaps WHERE gap_id = %s AND status = 'pending';", (gap_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Gap not found or already resolved.")

    question = rows[0]["question"]

    # Add the new Q&A pair to the live vector store immediately - no
    # re-ingestion of the whole document set needed, this is an
    # incremental add.
    vector_store = get_vector_store()
    vector_store.add_texts(
        texts=[f"Q: {question}\nA: {request.answer}"],
        metadatas=[{"source": f"admin_faq_gap_{gap_id}"}],
    )

    run_write(
        """
        UPDATE faq_gaps
        SET status = 'resolved', resolved_answer = %s, resolved_at = NOW()
        WHERE gap_id = %s;
        """,
        (request.answer, gap_id),
    )

    return {"status": "resolved", "gap_id": gap_id, "question": question}


@app.post("/admin/faq-gaps/{gap_id}/dismiss")
def dismiss_faq_gap(gap_id: int, admin_id: int = Depends(get_current_admin_id)):
    run_write("UPDATE faq_gaps SET status = 'dismissed' WHERE gap_id = %s;", (gap_id,))
    return {"status": "dismissed", "gap_id": gap_id}

# ---------- Orders & Tickets (direct data access, no LLM needed) ----------

@app.get("/orders")
def list_orders(customer_id: int = Depends(get_current_customer_id)):
    return run_query(
        "SELECT * FROM orders WHERE customer_id = %s ORDER BY order_date DESC;",
        (customer_id,),
    )


@app.get("/orders/{order_id}")
def get_order(order_id: int, customer_id: int = Depends(get_current_customer_id)):
    rows = run_query(
        "SELECT * FROM orders WHERE order_id = %s AND customer_id = %s;",
        (order_id, customer_id),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Order not found.")
    return rows[0]


class TicketRequest(BaseModel):
    issue: str
    order_id: int | None = None


@app.post("/tickets")
def create_ticket(request: TicketRequest, customer_id: int = Depends(get_current_customer_id)):
    from backend.app.tools.order_tools import create_support_ticket
    return create_support_ticket.invoke({
        "current_customer_id": customer_id,
        "issue": request.issue,
        "order_id": request.order_id,
    })


@app.get("/tickets")
def list_tickets(customer_id: int = Depends(get_current_customer_id)):
    return run_query(
        "SELECT * FROM support_tickets WHERE customer_id = %s ORDER BY created_at DESC;",
        (customer_id,),
    )