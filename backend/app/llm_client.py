from pydantic import SecretStr
from backend.app.config import settings

settings.validate()

# This is the one place in the whole project that constructs the LLM object.
# Every later phase (tools, agent, LangGraph) imports `llm` from here —
# they never care which provider is actually behind it.
if settings.LLM_PROVIDER == "groq":
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model=settings.LLM_MODEL,
        api_key=SecretStr(settings.GROQ_API_KEY),
        temperature=0.2,
    )
elif settings.LLM_PROVIDER == "openai":
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=SecretStr(settings.OPENAI_API_KEY),
        temperature=0.2,
    )
else:
    # settings.validate() already guards against this, but this keeps
    # the module self-contained if validate() is ever skipped.
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")