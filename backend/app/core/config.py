from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Primary AI: Anthropic Claude Opus ---
    ANTHROPIC_API_KEY: Optional[str] = None

    # --- Fallback AI: Groq (free tier, LLaMA) ---
    GROQ_API_KEY: Optional[str] = None
    MODEL: str = "llama-3.3-70b-versatile"  # used only if Groq fallback active
    MAX_TOKENS: int = 8096

    # --- SEC EDGAR ---
    SEC_USER_AGENT: str = "HedgeOS research@hedgeos.ai"

    # --- Reddit (Phase 2 sentiment) ---
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "hedgeos_research_v1"

    # --- Flask (Phase 4 crew runner) ---
    FLASK_ENV: str = "development"
    FLASK_PORT: int = 5000

    # --- FastAPI ---
    FASTAPI_PORT: int = 8000

    @property
    def use_anthropic(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)

    @property
    def anthropic_model(self) -> str:
        return "claude-opus-4-6"

    class Config:
        env_file = ".env"


settings = Settings()
