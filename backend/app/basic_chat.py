from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.llm_client import llm

SYSTEM_PROMPT = (
    "You are a helpful customer support assistant for an e-commerce "
    "company. Answer clearly and concisely. If you don't know something "
    "specific about a customer's order or account, say so honestly "
    "instead of guessing."
)


def ask(user_message: str) -> str:
    """
    Send a single user message to the LLM, with a fixed system prompt,
    and return the text response.

    No memory, no tools — just: message in, message out.
    """
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    try:
        response = llm.invoke(messages)
    except Exception as e:
        # We don't yet know every failure mode we'll hit (auth, rate limit,
        # network) — so for now we catch broadly, log clearly, and re-raise
        # a message a caller can actually act on. We'll narrow this as we
        # learn which exceptions actually show up.
        raise RuntimeError(f"LLM call failed: {e}") from e

    return response.content


if __name__ == "__main__":
    # Quick manual test from the command line
    print("Customer Support Assistant (Phase 2 — no tools, no memory)")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            break

        reply = ask(user_input)
        print(f"Assistant: {reply}\n")