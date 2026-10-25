import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from backend.app.rag.ingest import VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME


def run_retrieval_eval(k: int = 3):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vector_store = Chroma(
        persist_directory=VECTOR_STORE_DIR,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )

    with open("evaluation/eval_set.json") as f:
        eval_set = json.load(f)

    cases = [c for c in eval_set if "expected_source_doc" in c]
    if not cases:
        print("No retrieval cases found in eval_set.json (need 'expected_source_doc' field).")
        return

    hits = 0
    for case in cases:
        results = vector_store.similarity_search(case["query"], k=k)
        sources = [r.metadata.get("source") for r in results]
        hit = case["expected_source_doc"] in sources
        hits += hit
        status = "HIT" if hit else "MISS"
        print(f"[{status}] {case['id']}: expected={case['expected_source_doc']}, got={sources}")

    print(f"\nRecall@{k}: {hits}/{len(cases)} ({100 * hits / len(cases):.1f}%)")


if __name__ == "__main__":
    run_retrieval_eval()