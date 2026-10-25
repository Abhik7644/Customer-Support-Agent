from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from backend.app.rag.ingest import VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME


def get_vector_store() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return Chroma(persist_directory=VECTOR_STORE_DIR, embedding_function=embeddings)


def test_retrieval_finds_return_policy():
    vector_store = get_vector_store()
    results = vector_store.similarity_search("Can I return a product after 20 days?", k=2)
    assert len(results) > 0
    sources = [r.metadata.get("source") for r in results]
    assert "return_policy.pdf" in sources


if __name__ == "__main__":
    vector_store = get_vector_store()

    queries = [
        "Can I return a product after 20 days?",
        "How long does shipping take?",
        "Is my product covered under warranty?",
        "money back if I don't like it",
    ]

    for q in queries:
        print(f"\nQuery: {q}")
        results = vector_store.similarity_search(q, k=2)
        for r in results:
            print(f"  [{r.metadata.get('source')}] {r.page_content[:100]}...")