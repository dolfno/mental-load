"""Integration tests for API endpoints."""

import os
import tempfile
from datetime import date

import pytest
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

from src.infrastructure import Database, set_database
from src.presentation.main import app


@pytest.fixture
def test_db():
    """Create a temporary test database with actual migrations."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Run actual alembic migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(alembic_cfg, "head")

    db = Database(path)
    set_database(db)

    yield db

    os.unlink(path)


@pytest.fixture
def client(test_db):
    """Create test client with test database."""
    return TestClient(app)


class TestTaskEndpoints:
    def test_create_task(self, client):
        response = client.post(
            "/api/tasks",
            json={
                "name": "Test Task",
                "recurrence": {"type": "daily"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Task"
        assert data["id"] is not None

    def test_list_tasks(self, client):
        # Create a task first
        client.post(
            "/api/tasks",
            json={"name": "Task 1", "recurrence": {"type": "daily"}},
        )

        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Task 1"

    def test_update_task(self, client):
        # Create task
        create_response = client.post(
            "/api/tasks",
            json={"name": "Original", "recurrence": {"type": "daily"}},
        )
        task_id = create_response.json()["id"]

        # Update task
        response = client.put(f"/api/tasks/{task_id}", json={"name": "Updated"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_update_nonexistent_task(self, client):
        response = client.put("/api/tasks/9999", json={"name": "Updated"})
        assert response.status_code == 404

    def test_delete_task(self, client):
        # Create task
        create_response = client.post(
            "/api/tasks",
            json={"name": "To Delete", "recurrence": {"type": "daily"}},
        )
        task_id = create_response.json()["id"]

        # Delete task
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

        # Task should still exist but be inactive
        all_tasks = client.get("/api/tasks?active_only=false").json()
        deleted_task = next((t for t in all_tasks if t["id"] == task_id), None)
        assert deleted_task is not None
        assert deleted_task["is_active"] is False

    def test_complete_task(self, client):
        # Create task
        create_response = client.post(
            "/api/tasks",
            json={
                "name": "Complete Me",
                "recurrence": {"type": "weekly"},
                "next_due": str(date.today()),
            },
        )
        task_id = create_response.json()["id"]

        # Create member
        member_response = client.post("/api/members", json={"name": "John"})
        member_id = member_response.json()["id"]

        # Complete task
        response = client.post(
            f"/api/tasks/{task_id}/complete",
            json={"member_id": member_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["last_completed"] is not None
        assert data["next_due"] is not None

    def test_get_urgent_tasks(self, client):
        # Create urgent task (due today)
        client.post(
            "/api/tasks",
            json={
                "name": "Urgent Task",
                "recurrence": {"type": "daily"},
                "next_due": str(date.today()),
            },
        )

        # Create non-urgent task
        from datetime import timedelta

        future_date = date.today() + timedelta(days=10)
        client.post(
            "/api/tasks",
            json={
                "name": "Not Urgent",
                "recurrence": {"type": "weekly"},
                "next_due": str(future_date),
            },
        )

        response = client.get("/api/tasks/urgent")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(t["calculated_urgency"] == "high" for t in data)


class TestMemberEndpoints:
    def test_create_member(self, client):
        response = client.post("/api/members", json={"name": "John"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John"
        assert data["id"] is not None

    def test_list_members(self, client):
        client.post("/api/members", json={"name": "John"})
        client.post("/api/members", json={"name": "Jane"})

        response = client.get("/api/members")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_delete_member(self, client):
        create_response = client.post("/api/members", json={"name": "ToDelete"})
        member_id = create_response.json()["id"]

        response = client.delete(f"/api/members/{member_id}")
        assert response.status_code == 204


class TestHistoryEndpoints:
    def test_get_history(self, client):
        # Create task and member
        task_response = client.post(
            "/api/tasks",
            json={"name": "History Task", "recurrence": {"type": "daily"}},
        )
        task_id = task_response.json()["id"]

        member_response = client.post("/api/members", json={"name": "John"})
        member_id = member_response.json()["id"]

        # Complete task
        client.post(f"/api/tasks/{task_id}/complete", json={"member_id": member_id})

        # Get history
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["task_name"] == "History Task"
        assert data[0]["completed_by_name"] == "John"


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
