import asyncio
from backend.app.agent_v2 import builder
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

graph = builder.compile(checkpointer=InMemorySaver())

async def main():
    config: RunnableConfig = {
        "configurable": {"thread_id": "debug-vague-order", "current_customer_id": 1}
    }
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="Where is my order?")]},
        config=config,
    )
    print(result["messages"][-1].content)

asyncio.run(main())