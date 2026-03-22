from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import research

app = FastAPI(
    title="AlphaOS",
    description=(
        "Agentic AI research platform for hedge funds. "
        "Automates deep-dive company research and surfaces market edges."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten to specific origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router, prefix="/api/v1", tags=["research"])


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "version": "0.1.0"}
