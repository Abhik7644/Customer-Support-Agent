import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Central place to read configuration.
    Nothing in this project should call os.getenv() directly elsewhere —
    everything goes through this class.
    """
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "support_agent_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    def validate(self) -> None:
        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY is not set. Add it to .env.")
        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            raise ValueError(
                "LLM_PROVIDER is 'groq' but GROQ_API_KEY is not set."
            )
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise ValueError(
                "LLM_PROVIDER is 'openai' but OPENAI_API_KEY is not set."
            )
        if self.LLM_PROVIDER not in ("groq", "openai"):
            raise ValueError(f"Unknown LLM_PROVIDER '{self.LLM_PROVIDER}'.")
        if not self.DB_PASSWORD:
            raise ValueError(
                "DB_PASSWORD is not set. Add it to .env."
            )


settings = Settings()