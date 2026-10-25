from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt,Command
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from backend.app.llm_client import llm
from backend.app.database import run_query
from backend.app.tools.product_tools import get_product_details
from backend.app.tools.rag_tools import search_knowledge_base
from backend.app.tools.order_tools import (
    get_my_orders,
    get_order_status,
    check_refund_status,
    check_refund_eligibility,
    create_refund_request,
    create_support_ticket,
)

REFUND_APPROVAL_THRESHOLD = 5000.00

TOOLS = [
    get_product_details,
    search_knowledge_base,
    get_my_orders,
    get_order_status,
    check_refund_status,
    check_refund_eligibility,
    create_refund_request,
    create_support_ticket,
]

TOOLS_BY_NAME = {t.name: t for t in TOOLS}
CUSTOMER_SCOPED_TOOLS = {
    "get_my_orders",
    "get_order_status",
    "check_refund_status",
    "check_refund_eligibility",
    "create_refund_request",
    "create_support_ticket",
}
def run_tools(state: MessagesState,config : RunnableConfig) -> dict:
    """
    Custom tool-execution node, replacing the prebuilt ToolNode.

    We need this instead of ToolNode because several tools require
    current_customer_id - a value that must come from OUR authenticated
    session context, never from the LLM's tool call arguments. This is
    the concrete mechanism behind "don't trust the LLM with access
    control": we silently inject the real value and ignore/override
    anything the model might have guessed for that argument.
    """
    configurable=config.get("configurable") or {}
    current_customer_id= configurable["current_customer_id"]
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        # Shouldn't normally happen - tools_condition only routes here
        # when tool_calls exist - but this keeps the function honest
        # about its own assumptions, and satisfies the type checker.
        return {"messages": []}
    tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = dict(tool_call["args"])  # copy, don't mutate the original
        tool_call_id = tool_call["id"]

        if tool_name in CUSTOMER_SCOPED_TOOLS:
            tool_args["current_customer_id"] = current_customer_id

        tool_to_run = TOOLS_BY_NAME.get(tool_name)
        if tool_to_run is None:
            result = {"error": f"Unknown tool requested: {tool_name}"}
        else:
            result = tool_to_run.invoke(tool_args)

        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=tool_call_id)
        )

    return {"messages": tool_messages}

llm_with_tools = llm.bind_tools(TOOLS)

def review_refund(state: MessagesState, config: RunnableConfig) -> dict:
    """
    Sits between the agent deciding to create a refund and the refund
    actually being created. If the requested amount exceeds the
    threshold, this pauses the ENTIRE graph and waits for a human
    decision before continuing.
    """
    last_message = state["messages"][-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    # Find the create_refund_request call, if there is one, and check
    # its amount against the threshold BEFORE it actually runs.
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "create_refund_request":
            order_id = tool_call["args"].get("order_id")

            # We need the order amount to decide - look it up directly,
            # since the tool call itself hasn't run yet at this point.
            order_rows = run_query(
                "SELECT total_amount FROM orders WHERE order_id = %s;",
                (order_id,),
            )
            amount = float(order_rows[0]["total_amount"]) if order_rows else 0.0

            if amount > REFUND_APPROVAL_THRESHOLD:
                decision = interrupt({
                    "action": "approve_refund",
                    "order_id": order_id,
                    "amount": amount,
                    "message": f"Refund of ₹{amount} for order {order_id} exceeds the ₹{REFUND_APPROVAL_THRESHOLD} threshold and requires human approval.",
                })

                if decision.get("approved") is not True:
                    # Human rejected it - don't run the tool at all.
                    # We inject a fake ToolMessage explaining the rejection,
                    # so the agent's next turn can explain this to the customer.
                    return {
                        "messages": [
                            ToolMessage(
                                content=f"Refund request for order {order_id} was reviewed and NOT approved by a human agent.",
                                tool_call_id=tool_call["id"],
                            )
                        ]
                    }

    # Either no refund tool call, or it was approved, or under threshold -
    # proceed to actually run the tools normally.
    return {"messages": []}

SYSTEM_PROMPT = (
    "You are a helpful customer support assistant for an e-commerce "
    "company. You have access to tools for looking up product "
    "information, searching company policies, and checking a "
    "customer's own orders, refunds, and support tickets.\n\n"
    "For refund requests: first check the order's status, then use "
    "check_refund_eligibility before ever calling create_refund_request. "
    "Never call create_refund_request without first confirming "
    "eligibility. If an order isn't eligible, explain why clearly "
    "rather than creating the request anyway.\n\n"
    "Use a tool whenever the customer asks something a tool can "
    "answer — don't guess at product details, policies, or order "
    "information you don't actually have. If no tool is relevant, "
    "answer normally.\n\n"
    "Formatting: respond in short, plain conversational paragraphs. "
    "Avoid markdown tables and heavy formatting unless the customer "
    "specifically asks for a structured breakdown or comparison."
)




def call_model(state: MessagesState, config: RunnableConfig) -> dict:
    """
    The 'agent' node: sends the current message history to the LLM
    (with tools bound) and returns its response as a state update.

    MessagesState's built-in reducer APPENDS this to the existing
    message list - we don't need to manage that merge ourselves.
    """
    messages = state["messages"]

    # Prepend the system prompt only if it's not already there
    # (keeps this node safe to call repeatedly without duplicating it)
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    if isinstance(response, AIMessage) and response.tool_calls:
        print(f"[DEBUG] Tool call(s): {[tc['name'] for tc in response.tool_calls]}")
    return {"messages": [response]}


# --- Build the graph ---
builder = StateGraph(MessagesState)

builder.add_node("agent", call_model)
builder.add_node("review_refund", review_refund)
builder.add_node("tools", run_tools)

builder.add_edge(START, "agent")

# tools_condition is a LangGraph-provided routing function: it checks
# the last message for tool_calls and returns "tools" or END
# accordingly. This replaces the `if ai_response.tool_calls:` check we
# wrote by hand in agent_v1.py.
builder.add_conditional_edges("agent", tools_condition, {"tools": "review_refund", "__end__": END})

# After running tools, always go back to the agent so it can see the
# tool result and decide what to do next (answer, or call another tool).
builder.add_edge("review_refund","tools")
builder.add_edge("tools", "agent")

#graph = builder.compile(checkpointer=InMemorySaver())


def run_agent_interactive():
    """
    Interactive CLI loop that handles both normal turns AND
    human-approval interrupts.
    """
    from langchain_core.messages import HumanMessage
    thread_id=input("Enter a session ID: ").strip()
    customer_id=int(input("Enter a Customer ID to stimulate (e.g, 1,2, or 3): ").strip())
    config: RunnableConfig = {
        "configurable":{
            "thread_id": thread_id,
            "current_customer_id": customer_id,
            }
        }
    
    print("Customer Support Agent (Phase 12 — human-in-the-loop)")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            break

        result = graph.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        if "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value
            print(f"\n[APPROVAL NEEDED] {interrupt_data['message']}")
            decision_input = input("Approve this refund? (yes/no): ").strip().lower()
            approved = decision_input == "yes"

            result = graph.invoke(
                Command(resume={"approved": approved}),
                config=config,
            )

        final_message = result["messages"][-1]
        print(f"Assistant: {final_message.content}\n")


if __name__ == "__main__":
    graph = builder.compile(checkpointer=InMemorySaver())
    run_agent_interactive()