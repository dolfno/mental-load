import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure import create_default_admin_if_needed
from .routes import tasks_router, members_router, history_router, auth_router, admin_router, notes_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default CORS origins for local development
DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

def get_cors_origins() -> list[str]:
    """Get CORS origins from environment variable or use defaults."""
    cors_env = os.getenv("CORS_ORIGINS")
    if cors_env:
        # Parse comma-separated list, strip whitespace
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    return DEFAULT_CORS_ORIGINS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting Aivin application...")
    create_default_admin_if_needed()
    yield
    # Shutdown
    logger.info("Shutting down Aivin application...")


app = FastAPI(
    title="Aivin",
    description="Household task management system",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(tasks_router)
app.include_router(members_router)
app.include_router(history_router)
app.include_router(notes_router)


@app.get("/")
def root():
    return {"message": "Welcome to Aivin - Household Task Management"}


@app.get("/health")
@app.get("/healthz")
def health():
    return {"status": "healthy"}
