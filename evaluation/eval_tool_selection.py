import json
import asyncio
import time
from backend.app.agent_v2 import builder
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

# Eval runs use their own throwaway in-memory graph, completely separate
# from the real app's persistent Postgres checkpointer - eval runs
# should never touch real customer conversation history, and shouldn't
# need a database connection just to test tool routing.
eval_graph = builder.compile(checkpointer=InMemorySaver())


async def get_run_trace(query: str, customer_id: int, run_tag: str) -> dict:
    config: RunnableConfig = {
        "configurable": {
            "thread_id": f"eval-{run_tag}",
            "current_customer_id": customer_id,
        }
    }
    tool_calls_seen = []
    interrupted = False

    async for mode, chunk in eval_graph.astream(
        {"messages": [HumanMessage(content=query)]},
        config=config,
        stream_mode=["updates"],
    ):
        if isinstance(chunk, dict):
            if "agent" in chunk:
                last_msg = chunk["agent"]["messages"][-1]
                if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                    tool_calls_seen.extend(tc["name"] for tc in last_msg.tool_calls)
            if "__interrupt__" in chunk:
                interrupted = True

    return {"tools": tool_calls_seen, "interrupted": interrupted}


async def run_tool_selection_eval():
    with open("evaluation/eval_set.json") as f:
        eval_set = json.load(f)

    run_stamp = str(int(time.time()))
    correct = 0
    total = 0
    results = []

    for case in eval_set:
        if "expected_tool" not in case and "expected_tools_in_order" not in case and "forbidden_tool" not in case:
            continue

        total += 1
        customer_id = case.get("requires_customer_id", 1)
        run_tag = f"{case['id']}-{run_stamp}"

        run_result = await get_run_trace(case["query"], customer_id, run_tag)
        actual_tools = run_result["tools"]
        interrupted = run_result["interrupted"]

        if "expected_tools_in_order" in case:
            passed = actual_tools[: len(case["expected_tools_in_order"])] == case["expected_tools_in_order"]
        elif "expected_tool" in case:
            passed = (case["expected_tool"] is None and len(actual_tools) == 0) or (case["expected_tool"] in actual_tools)
        else:
            passed = True

        if "forbidden_tool" in case and case["forbidden_tool"] in actual_tools:
            passed = False

        if case.get("expect_interrupt") and not interrupted:
            passed = False

        if passed:
            correct += 1

        results.append({
            "id": case["id"],
            "query": case["query"],
            "expected": case.get("expected_tool", case.get("expected_tools_in_order")),
            "actual": actual_tools,
            "interrupted": interrupted,
            "passed": passed,
        })

    print(f"\nTool Selection Accuracy: {correct}/{total} ({100 * correct / total:.1f}%)\n")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['id']}: expected={r['expected']}, actual={r['actual']}, interrupted={r['interrupted']}")

    return results


if __name__ == "__main__":
    asyncio.run(run_tool_selection_eval())