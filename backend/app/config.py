import os
from dotenv import load_dotenv

# Load variables from .env into the process environment
load_dotenv()


class Settings:
    """
    Central place to read configuration.
    Nothing in this project should call os.getenv() directly elsewhere —
    everything goes through this class, so there's one place to see
    every config value the app depends on.
    """
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    def validate(self) -> None:
        """Fail loudly at startup if required config is missing."""
        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            raise ValueError(
                "LLM_PROVIDER is 'groq' but GROQ_API_KEY is not set. "
                "Copy .env.example to .env and fill in your Groq key."
            )
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError(
                "LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set."
            )
        if self.LLM_PROVIDER not in ("groq", "openai"):
            raise ValueError(
                f"Unknown LLM_PROVIDER '{self.LLM_PROVIDER}'. "
                "Expected 'groq' or 'openai'."
            )


settings = Settings()