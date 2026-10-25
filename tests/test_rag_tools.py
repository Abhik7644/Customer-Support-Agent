from backend.app.tools.rag_tools import search_knowledge_base


def test_finds_return_policy():
    result = search_knowledge_base.invoke({"query": "Can I return a product after 20 days?"})
    assert "return_policy.pdf" in result


def test_no_crash_on_odd_query():
    result = search_knowledge_base.invoke({"query": "purple elephant tax law"})
    # Should still return SOMETHING (the closest matches, even if not great)
    # rather than crashing - similarity search always returns its k nearest
    # neighbors, even if none are a great match.
    assert isinstance(result, str)
    assert len(result) > 0


if __name__ == "__main__":
    print(search_knowledge_base.invoke({"query": "What's your return policy?"}))