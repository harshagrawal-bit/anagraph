from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Primary AI: OpenRouter (Claude/GPT-4/Gemini via single API) ---
    OPEN_ROUTER_API_KEY: Optional[str] = None
    OPEN_ROUTER_MODEL: str = "anthropic/claude-opus-4-5"

    # --- Anthropic direct (needed for web_search tool in data_fetcher) ---
    ANTHROPIC_API_KEY: Optional[str] = None

    # --- Fallback AI: Groq (free tier, LLaMA) ---
    GROQ_API_KEY: Optional[str] = None
    MODEL: str = "llama-3.3-70b-versatile"
    MAX_TOKENS: int = 4096

    # --- SEC EDGAR ---
    SEC_USER_AGENT: str = "HedgeOS research@hedgeos.ai"

    # --- Reddit (Phase 2 sentiment) ---
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "hedgeos_research_v1"

    # --- Flask ---
    FLASK_ENV: str = "development"
    FLASK_PORT: int = 5000

    # --- FastAPI ---
    FASTAPI_PORT: int = 8000

    @property
    def active_model(self) -> str:
        if self.OPEN_ROUTER_API_KEY:
            return self.OPEN_ROUTER_MODEL
        if self.ANTHROPIC_API_KEY:
            return "claude-opus-4-6"
        return self.MODEL  # Groq fallback

    @property
    def use_openrouter(self) -> bool:
        return bool(self.OPEN_ROUTER_API_KEY)

    @property
    def use_anthropic(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)

    class Config:
        env_file = ".env"


settings = Settings()
