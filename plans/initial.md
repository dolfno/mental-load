# Aivin - Household Task Management System

## Overview
A web application to manage household chores and reduce mental load. Single shared household view with task tracking, recurring schedules, and urgency indicators.

## Tech Stack
- **Backend**: Python with FastAPI, Clean Architecture
- **Frontend**: TypeScript with React (Vite) + Tailwind CSS
- **Database**: SQLite with raw sqlite3 + dataclasses (no ORM)
- **Migrations**: Alembic (standalone, no SQLAlchemy ORM)
- **Testing**: pytest
- **Package Manager**: uv

## Backend Architecture (Clean Architecture by Layer)

```
backend/
├── pyproject.toml           # uv project config
├── alembic/                  # Database migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── src/
│   ├── domain/               # Business entities & rules (no dependencies)
│   │   ├── entities.py       # Task, HouseholdMember, TaskCompletion dataclasses
│   │   ├── value_objects.py  # RecurrencePattern, Urgency
│   │   └── services.py       # Pure business logic (due date calculation)
│   │
│   ├── application/          # Use cases (depends on domain)
│   │   ├── interfaces.py     # Repository interfaces (abstractions)
│   │   ├── task_usecases.py  # CreateTask, CompleteTask, GetUrgentTasks
│   │   └── member_usecases.py
│   │
│   ├── infrastructure/       # External concerns (depends on application)
│   │   ├── database.py       # SQLite connection management
│   │   ├── repositories.py   # Concrete repository implementations
│   │   └── task_importer.py  # Import from tasks.md
│   │
│   └── presentation/         # API layer (depends on application)
│       ├── main.py           # FastAPI app
│       ├── routes/
│       │   ├── tasks.py
│       │   ├── members.py
│       │   └── history.py
│       └── schemas.py        # Pydantic request/response models
│
└── tests/
    ├── unit/
    │   ├── test_domain.py    # Test business logic
    │   └── test_usecases.py  # Test use cases with mocked repos
    └── integration/
        └── test_api.py       # Test API endpoints
```

## Frontend Structure

```
frontend/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── TaskList.tsx
│   │   ├── TaskCard.tsx
│   │   ├── AddTaskForm.tsx
│   │   └── MemberSelector.tsx
│   ├── api.ts
│   └── types.ts
├── package.json
└── vite.config.ts
```

## Data Model (Domain Entities)

### Task
```python
@dataclass
class Task:
    id: int | None
    name: str
    recurrence: RecurrencePattern
    urgency_label: Urgency | None  # manual override
    last_completed: datetime | None
    next_due: date | None
    is_active: bool = True
```

### RecurrencePattern (Value Object)
```python
@dataclass
class RecurrencePattern:
    type: RecurrenceType  # daily, weekly, biweekly, monthly, quarterly, yearly, continuous
    days: list[int] | None  # for weekly: [0=Mon, 6=Sun]
    interval: int = 1  # every X days/weeks/months
    time_of_day: str | None  # morning, evening
```

### HouseholdMember
```python
@dataclass
class HouseholdMember:
    id: int | None
    name: str
```

### TaskCompletion
```python
@dataclass
class TaskCompletion:
    id: int | None
    task_id: int
    completed_at: datetime
    completed_by_id: int
```

## Database Schema (Alembic Migrations)

```sql
-- tasks table
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    recurrence_type TEXT NOT NULL,
    recurrence_days TEXT,  -- JSON array
    recurrence_interval INTEGER DEFAULT 1,
    time_of_day TEXT,
    urgency_label TEXT,
    last_completed TIMESTAMP,
    next_due DATE,
    is_active BOOLEAN DEFAULT 1
);

-- household_members table
CREATE TABLE household_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- task_completions table
CREATE TABLE task_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    completed_at TIMESTAMP NOT NULL,
    completed_by_id INTEGER NOT NULL REFERENCES household_members(id)
);
```

## Urgency Calculation (Domain Service)
- **High**: `urgency_label=high` OR overdue OR due today
- **Medium**: `urgency_label=medium` OR due in 1-3 days
- **Low**: everything else
- **Continuous tasks**: Always visible, no due date

## Recurrence Patterns (from tasks.md)
| Pattern | Example | Type + Config |
|---------|---------|---------------|
| Elke dag | Flessen reinigen | `daily` |
| Elke ochtend/avond | Ontbijt maken | `daily` + time_of_day |
| Specific days | Zondag, Ma do | `weekly` + days=[0,3] |
| X keer per week | 2 keer per week | `weekly` + interval |
| Elke twee weken | Bed verschonen | `biweekly` |
| Elke maand | Laadjes netjes | `monthly` |
| Elke X maanden | Elke drie maanden | `monthly` + interval=3 |
| X keer per jaar | 3 keer per jaar | `yearly` + interval |
| Continu | Kledingkast managen | `continuous` |

## API Endpoints

```
# Tasks
GET  /api/tasks              # List all tasks with urgency status
GET  /api/tasks/urgent       # High urgency tasks
GET  /api/tasks/upcoming     # Due in next 7 days
POST /api/tasks              # Create task
PUT  /api/tasks/{id}         # Update task
POST /api/tasks/{id}/complete # Mark complete (body: {member_id})
DELETE /api/tasks/{id}       # Soft delete (deactivate)

# Members
GET  /api/members            # List household members
POST /api/members            # Add member
DELETE /api/members/{id}     # Remove member

# History
GET  /api/history            # Completion history
```

## Implementation Steps

1. **Backend foundation**
   - Initialize uv project
   - Set up Alembic with initial migration
   - Create domain layer (entities, value objects, services)
   - Create application layer (interfaces, use cases)
   - Create infrastructure layer (SQLite repositories)

2. **Backend API**
   - FastAPI routes
   - Pydantic schemas
   - Wire up dependency injection

3. **Backend testing**
   - Unit tests for domain logic
   - Unit tests for use cases with mocked repos

4. **Task importer**
   - Parse tasks.md and import to database

5. **Frontend**
   - Initialize Vite + React + TypeScript + Tailwind
   - Dashboard component
   - Task list and completion flow
   - Add/edit forms

## Verification
1. Run migrations: `cd backend && alembic upgrade head`
2. Run tests: `cd backend && uv run pytest`
3. Run backend: `cd backend && uv run uvicorn src.presentation.main:app --reload`
4. Run frontend: `cd frontend && npm run dev`
5. Import tasks: `cd backend && uv run python -m src.infrastructure.task_importer`
6. Verify: Create member, view tasks, complete a task, check history
