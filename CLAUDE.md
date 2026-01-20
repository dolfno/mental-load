# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aivin** is a household task management system to reduce mental load by tracking recurring chores, managing task assignments, and monitoring completion. Full-stack app with Python/FastAPI backend and React/TypeScript frontend.

## Development Commands

### Backend (in `/backend`)
```bash
uv sync                                              # Install dependencies
uv run alembic upgrade head                                 # Run database migrations
uv run pytest                                        # Run all tests
uv run uvicorn src.presentation.main:app --reload   # Dev server (port 8000)
```

### Frontend (in `/frontend`)
```bash
npm install          # Install dependencies
npm run dev          # Dev server (port 5173, proxies /api to backend)
npm run build        # TypeScript check + production build
npm run lint         # ESLint
```

## Architecture

### Backend - Clean Architecture
```
backend/src/
├── domain/          # Pure business rules, no dependencies
│   ├── entities.py      # Task, HouseholdMember, TaskCompletion
│   ├── value_objects.py # RecurrencePattern, Urgency, RecurrenceType, TimeOfDay
│   └── services.py      # Due date calculation, urgency calculation
├── application/     # Use cases, depends only on domain
│   ├── interfaces.py    # Repository abstractions
│   ├── task_usecases.py
│   └── member_usecases.py
├── infrastructure/  # External dependencies
│   ├── database.py      # SQLite (local) / Turso HTTP API (prod)
│   ├── repositories.py  # Concrete repository implementations
│   └── task_importer.py # Parse tasks.md into database
└── presentation/    # FastAPI layer
    ├── main.py          # App setup with CORS
    ├── routes/          # API endpoints
    └── schemas.py       # Pydantic models
```

### Frontend
```
frontend/src/
├── components/      # React components (Dashboard, TaskList, TaskCard, etc.)
├── api.ts          # Typed fetch wrapper
├── types.ts        # TypeScript types mirroring backend
└── App.tsx
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

Tables: `tasks`, `household_members`, `task_completions`, `notes`

## API

Base URL: `/api`

- `GET/POST /api/tasks` - List/create tasks
- `POST /api/tasks/{id}/complete` - Mark task complete (body: `{member_id}`)
- `GET /api/tasks/urgent` - High urgency tasks
- `GET /api/members` - List household members
- `GET /api/history` - Task completion history

## Workflow

Commit in between completion of tasks.
