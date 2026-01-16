from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import tasks_router, members_router, history_router

app = FastAPI(
    title="Aivin",
    description="Household task management system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
def health():
    return {"status": "healthy"}
