from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from backend.app.rag.ingest import VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME
from backend.app.database import run_write

_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
_vector_store = Chroma(
    persist_directory=VECTOR_STORE_DIR,
    embedding_function=_embeddings,
)

# Below this relevance score (0-1, higher = more relevant), we treat the
# knowledge base as NOT having a real answer, rather than returning a
# loosely-related chunk as if it were useful. This threshold is empirical -
# tune it based on real query testing, not a theoretically "correct" number.
RELEVANCE_THRESHOLD = 0.3


def get_vector_store() -> Chroma:
    """Shared accessor so admin/FAQ-update code uses the exact same
    live vector store instance as the tool, not a second, separately
    loaded copy."""
    return _vector_store


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the company's policy documents (return, refund, shipping,
    cancellation, warranty policies, and product FAQ) for information
    relevant to the customer's question.

    Use this whenever the customer asks about company POLICIES or
    RULES. Do NOT use this for questions about a specific customer's
    own orders, refunds, or account.

    Args:
        query: The customer's question, in their own words.

    Returns:
        The most relevant policy text found, or an explicit statement
        that no relevant information was found.
    """
    results_with_scores = _vector_store.similarity_search_with_relevance_scores(query, k=3)

    relevant = [(doc, score) for doc, score in results_with_scores if score >= RELEVANCE_THRESHOLD]

    if not relevant:
        # Log this as a genuine knowledge gap for admin review, not just
        # a failed search - this is the data source the self-updating
        # part of this feature runs on.
        try:
            run_write(
                "INSERT INTO faq_gaps (question) VALUES (%s);",
                (query,),
            )
        except Exception:
            pass  # logging the gap should never break the actual chat response

        return (
            "No relevant information was found in the knowledge base for "
            "this question. Let the customer know you don't have this "
            "information yet, and offer to create a support ticket so a "
            "human can follow up."
        )

    formatted_chunks = []
    for doc, score in relevant:
        source = doc.metadata.get("source", "unknown")
        formatted_chunks.append(f"[Source: {source}]\n{doc.page_content}")

    return "\n\n---\n\n".join(formatted_chunks)