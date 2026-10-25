from backend.app.llm_client import llm
from langchain_core.messages import SystemMessage, HumanMessage

JUDGE_PROMPT = """You are evaluating whether an AI assistant's answer is grounded in the provided evidence.

Evidence (retrieved/tool output the assistant had access to):
{evidence}

Assistant's final answer:
{answer}

Does the answer make any claims NOT supported by the evidence above? Respond with exactly one word first: GROUNDED or UNGROUNDED, then a one-sentence reason."""


def check_groundedness(evidence: str, answer: str) -> dict:
    messages = [
        SystemMessage(content="You are a strict, careful evaluator."),
        HumanMessage(content=JUDGE_PROMPT.format(evidence=evidence, answer=answer)),
    ]
    response = llm.invoke(messages)
    content = response.content.strip()
    verdict = "UNGROUNDED" if content.upper().startswith("UNGROUNDED") else "GROUNDED"
    return {"verdict": verdict, "reasoning": content}


TEST_CASES = [
    {
        "id": "fabricated_60_day_window",
        "evidence": "Return window: 30 days from delivery. Electronics: 15 days.",
        "answer": "You can return any item within 60 days, no questions asked.",
        "expected_verdict": "UNGROUNDED",
    },
    {
        "id": "accurate_return_summary",
        "evidence": "Return window: 30 days from delivery. Electronics: 15 days.",
        "answer": "Most items can be returned within 30 days of delivery.",
        "expected_verdict": "GROUNDED",
    },
    {
        "id": "gift_wrap_with_added_claim",
        "evidence": "Q: gift options gift wrapping gift cards do you offer gifts\nA: Sorry but this is a customer support system we take queries.",
        "answer": "We don't offer a gift-wrapping service at the moment. If you'd like, you can add a personalized note to your order at checkout, and we'll include it with the package.",
        "expected_verdict": "UNGROUNDED",
    },
]


def run_groundedness_eval():
    correct = 0
    for case in TEST_CASES:
        result = check_groundedness(case["evidence"], case["answer"])
        passed = result["verdict"] == case["expected_verdict"]
        correct += passed
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {case['id']}: expected={case['expected_verdict']}, got={result['verdict']}")
        print(f"        reasoning: {result['reasoning']}\n")

    print(f"Groundedness judge accuracy: {correct}/{len(TEST_CASES)} ({100 * correct / len(TEST_CASES):.1f}%)")


if __name__ == "__main__":
    run_groundedness_eval()