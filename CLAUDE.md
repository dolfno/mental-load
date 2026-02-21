# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aivin** is a household task management system to reduce mental load by tracking recurring chores, managing task assignments, and monitoring completion. Full-stack app with Python/FastAPI backend and React/TypeScript frontend.

## Development Commands

### Backend (in `/backend`)
```bash
uv sync                                              # Install dependencies
uv run alembic upgrade head                          # Run database migrations
uv run pytest                                        # Run all tests
uv run pytest tests/unit/                            # Run unit tests only
uv run pytest tests/integration/                     # Run integration tests only
uv run pytest tests/unit/test_domain.py -k "test_name"  # Run single test
uv run uvicorn src.presentation.main:app --reload   # Dev server (port 8000)
```

### Frontend (in `/frontend`)
```bash
npm install          # Install dependencies
npm run dev          # Dev server (port 5173, proxies /api to backend)
npm run build        # TypeScript check + production build
npm run lint         # ESLint
npm run test:e2e     # Run Playwright e2e tests
npm run test:e2e:ui  # Run e2e tests with interactive UI
```

## Architecture

### Backend - Clean Architecture
```
backend/src/
├── domain/          # Pure business rules, no dependencies
│   ├── entities.py      # Task, HouseholdMember, TaskCompletion, Note, ChatMessage
│   ├── value_objects.py # RecurrencePattern, Urgency, RecurrenceType, TimeOfDay
│   └── services.py      # Due date calculation, urgency calculation
├── application/     # Use cases, depends only on domain
│   ├── interfaces.py    # Repository abstractions
│   ├── task_usecases.py
│   ├── member_usecases.py
│   ├── note_usecases.py
│   └── chat_usecases.py
├── infrastructure/  # External dependencies
│   ├── database.py      # SQLite (local) / Turso HTTP API (prod)
│   ├── repositories.py  # Concrete repository implementations
│   ├── llm_service.py   # OpenAI-compatible LLM integration with function calling
│   └── task_importer.py # Parse tasks.md into database
└── presentation/    # FastAPI layer
    ├── main.py          # App setup with CORS
    ├── routes/          # API endpoints (tasks, members, auth, admin, notes, chat)
    └── schemas.py       # Pydantic models
```

### Frontend
```
frontend/src/
├── components/      # React components (Dashboard, TaskList, TaskCard, etc.)
├── api.ts          # Typed fetch wrapper
├── types.ts        # TypeScript types mirroring backend
└── App.tsx
frontend/e2e/        # Playwright e2e tests
```

### Key Design Decisions
- **No ORM**: Raw SQLite with dataclasses for explicit data handling
- **Alembic**: Standalone migrations (not tied to SQLAlchemy ORM)
- **Clean Architecture**: Domain logic isolated from infrastructure
- **Proxy setup**: Frontend dev server proxies `/api` to `http://localhost:8000`

## Database

- **Local dev/tests**: SQLite (via Alembic)
- **Production**: Turso (via HTTP API)

Migrations in `backend/alembic/versions/`.

### Running Migrations
```bash
uv run alembic upgrade head  # Auto-detects SQLite (local) or Turso (if env vars set)
```

Tables: `tasks`, `household_members`, `task_completions`, `notes`, `users`, `chat_messages`

## Test Strategy

### Backend Tests (`backend/tests/`)

**Unit Tests** (`tests/unit/`):
- `test_domain.py` - Pure domain logic tests (urgency calculation, due date calculation, recurrence patterns). No mocks needed - tests pure functions and dataclasses.
- `test_usecases.py` - Use case tests with mocked repositories. Tests business logic without infrastructure dependencies.
- `test_database.py` - Database-related unit tests.

**Integration Tests** (`tests/integration/`):
- `test_api.py` - Full API endpoint tests using FastAPI TestClient. Creates a temporary SQLite database with actual Alembic migrations for each test. Tests complete request/response cycles including authentication.

### Frontend E2E Tests (`frontend/e2e/`)

Playwright-based end-to-end tests that run against the full stack:
- `auth.spec.ts` - Login/authentication flows
- `notepad.spec.ts` - Shared household notepad functionality
- `task-actions.spec.ts` - Task CRUD, completion, postponing, deletion

E2E tests require backend running and use test user accounts created via admin API.

### Test Principles
- **Domain tests are pure**: No mocks, no I/O - just test business logic
- **Use case tests mock infrastructure**: Verify orchestration without real database
- **Integration tests use real migrations**: Ensures schema correctness
- **E2E tests cover user workflows**: Real browser interactions against full stack

## API

Base URL: `/api`. All endpoints except `/health` and `/api/auth/*` require JWT authentication.

**Tasks**
- `GET/POST /api/tasks` - List/create tasks
- `PUT/DELETE /api/tasks/{id}` - Update/delete task
- `POST /api/tasks/{id}/complete` - Mark task complete (body: `{member_id}`)
- `GET /api/tasks/urgent` - High urgency tasks

**Members & Notes**
- `GET/POST /api/members` - List/create household members
- `DELETE /api/members/{id}` - Delete member
- `GET/PUT /api/notes` - Get/update shared household note

**Auth & Admin**
- `POST /api/auth/login` - Login (returns JWT token)
- `GET /api/auth/me` - Get current user
- `POST /api/admin/users` - Create user (requires `X-Admin-Api-Key` header)

**History**
- `GET /api/history` - Task completion history

**Chat (AI Assistant)**
- `POST /api/chat` - Send message and get AI response
- `GET /api/chat/history` - Get chat message history
- `DELETE /api/chat/history` - Clear chat history

## Hosting / Deployment

- **Backend**: Render (free tier) — keep-alive cron pings `https://api.jorindeendolf.nl/health` every 14 min
- **Database**: Turso (production), local SQLite for dev/tests
- **Frontend**: Strato (SFTP deploy to `/aivin_html/`)

CI/CD via GitHub Actions (`.github/workflows/`):
- `deploy-frontend.yml` — builds and SFTPs frontend on push to `main`
- `keep-alive.yml` — pings Render health endpoint every 14 minutes

## Environment Variables

### Backend (`.env` in `/backend`)
```bash
# Auth (required)
JWT_SECRET_KEY=your-secret-key              # JWT signing key — generate with: openssl rand -hex 32
ADMIN_API_KEY=your-api-key-here             # Key for POST /api/admin/users (X-Admin-Api-Key header)
CORS_ORIGINS=http://localhost:5173          # Comma-separated allowed origins

# Auto-create admin user on startup (optional)
ADMIN_EMAIL=admin@example.com               # If set and user doesn't exist, creates admin on startup
ADMIN_PASSWORD=your-secure-password
ADMIN_NAME=Admin

# Database (optional — uses local SQLite if not set)
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-turso-token

# AI Chat (required for chat feature)
LLM_API_KEY=your-api-key                    # API key for OpenAI-compatible LLM provider
LLM_BASE_URL=https://api.openai.com/v1     # Base URL for LLM API (optional, defaults to OpenAI)
LLM_MODEL=gpt-4o-mini                      # Model name (optional, defaults to gpt-4o-mini)
```

### Frontend (build-time)
```bash
VITE_API_URL=https://api.jorindeendolf.nl   # Backend URL for production (defaults to /api for local dev)
```

### GitHub Actions Secrets
`SFTP_HOST`, `SFTP_USERNAME`, `SFTP_PASSWORD` — for Strato frontend deploy
`VITE_API_URL` — backend URL injected at build time

## Workflow

Commit in between completion of tasks.
