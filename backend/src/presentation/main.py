import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import tasks_router, members_router, history_router

# Default CORS origins for local development
DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

def get_cors_origins() -> list[str]:
    """Get CORS origins from environment variable or use defaults."""
    cors_env = os.getenv("CORS_ORIGINS")
    if cors_env:
        # Parse comma-separated list, strip whitespace
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    return DEFAULT_CORS_ORIGINS

app = FastAPI(
    title="Aivin",
    description="Household task management system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(members_router)
app.include_router(history_router)


@app.get("/")
def root():
    return {"message": "Welcome to Aivin - Household Task Management"}


@app.get("/health")
@app.get("/healthz")
def health():
    return {"status": "healthy"}
