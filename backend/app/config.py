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
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    def validate(self) -> None:
        """Fail loudly at startup if required config is missing."""
        if not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env "
                "and fill in your key."
            )


settings = Settings()