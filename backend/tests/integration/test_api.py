"""Integration tests for API endpoints."""

import os
import tempfile
from datetime import date
from unittest.mock import patch

import pytest
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

from src.infrastructure import Database, set_database
from src.presentation.main import app

# Test admin API key
TEST_ADMIN_API_KEY = "test-admin-api-key"


@pytest.fixture
def test_db():
    """Create a temporary test database with actual migrations."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Run actual alembic migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(alembic_cfg, "head")

    db = Database(path, use_turso=False)
    set_database(db)

    yield db

    # Reset singleton for next test
    set_database(None)
    os.unlink(path)


@pytest.fixture
def client(test_db):
    """Create test client with test database."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Create a user via admin API and return auth headers."""
    with patch.dict(os.environ, {"ADMIN_API_KEY": TEST_ADMIN_API_KEY}):
        # Create user via admin API
        response = client.post(
            "/api/admin/users",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "testpassword123",
            },
            headers={"X-Admin-Api-Key": TEST_ADMIN_API_KEY},
        )
        assert response.status_code == 201, f"User creation failed: {response.text}"

        # Login to get auth token
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


class TestTaskEndpoints:
    def test_create_task(self, client, auth_headers):
        response = client.post(
            "/api/tasks",
            json={
                "name": "Test Task",
                "recurrence": {"type": "daily"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Task"
        assert data["id"] is not None

    def test_list_tasks(self, client, auth_headers):
        # Create a task first
        client.post(
            "/api/tasks",
            json={"name": "Task 1", "recurrence": {"type": "daily"}},
            headers=auth_headers,
        )

        response = client.get("/api/tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Task 1"

    def test_update_task(self, client, auth_headers):
        # Create task
        create_response = client.post(
            "/api/tasks",
            json={"name": "Original", "recurrence": {"type": "daily"}},
            headers=auth_headers,
        )
        task_id = create_response.json()["id"]

        # Update task
        response = client.put(f"/api/tasks/{task_id}", json={"name": "Updated"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"

    def test_update_nonexistent_task(self, client, auth_headers):
        response = client.put("/api/tasks/9999", json={"name": "Updated"}, headers=auth_headers)
        assert response.status_code == 404

    def test_delete_task(self, client, auth_headers):
        # Create task
        create_response = client.post(
            "/api/tasks",
            json={"name": "To Delete", "recurrence": {"type": "daily"}},
            headers=auth_headers,
        )
        task_id = create_response.json()["id"]

        # Delete task
        response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 204

        # Task should still exist but be inactive
        all_tasks = client.get("/api/tasks?active_only=false", headers=auth_headers).json()
        deleted_task = next((t for t in all_tasks if t["id"] == task_id), None)
        assert deleted_task is not None
        assert deleted_task["is_active"] is False

    def test_complete_task(self, client, auth_headers):
        # Create task
        create_response = client.post(
            "/api/tasks",
            json={
                "name": "Complete Me",
                "recurrence": {"type": "weekly"},
                "next_due": str(date.today()),
            },
            headers=auth_headers,
        )
        task_id = create_response.json()["id"]

        # Create member
        member_response = client.post("/api/members", json={"name": "John"}, headers=auth_headers)
        member_id = member_response.json()["id"]

        # Complete task
        response = client.post(
            f"/api/tasks/{task_id}/complete",
            json={"member_id": member_id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["last_completed"] is not None
        assert data["next_due"] is not None

    def test_get_urgent_tasks(self, client, auth_headers):
        # Create urgent task (due today)
        client.post(
            "/api/tasks",
            json={
                "name": "Urgent Task",
                "recurrence": {"type": "daily"},
                "next_due": str(date.today()),
            },
            headers=auth_headers,
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
            headers=auth_headers,
        )

        response = client.get("/api/tasks/urgent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(t["calculated_urgency"] == "high" for t in data)


class TestMemberEndpoints:
    def test_create_member(self, client, auth_headers):
        response = client.post("/api/members", json={"name": "John"}, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John"
        assert data["id"] is not None

    def test_list_members(self, client, auth_headers):
        client.post("/api/members", json={"name": "John"}, headers=auth_headers)
        client.post("/api/members", json={"name": "Jane"}, headers=auth_headers)

        response = client.get("/api/members", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Includes 'Test User' from auth_headers fixture
        assert len(data) >= 3

    def test_delete_member(self, client, auth_headers):
        create_response = client.post("/api/members", json={"name": "ToDelete"}, headers=auth_headers)
        member_id = create_response.json()["id"]

        response = client.delete(f"/api/members/{member_id}", headers=auth_headers)
        assert response.status_code == 204


class TestHistoryEndpoints:
    def test_get_history(self, client, auth_headers):
        # Create task and member
        task_response = client.post(
            "/api/tasks",
            json={"name": "History Task", "recurrence": {"type": "daily"}},
            headers=auth_headers,
        )
        task_id = task_response.json()["id"]

        member_response = client.post("/api/members", json={"name": "John"}, headers=auth_headers)
        member_id = member_response.json()["id"]

        # Complete task
        client.post(f"/api/tasks/{task_id}/complete", json={"member_id": member_id}, headers=auth_headers)

        # Get history
        response = client.get("/api/history", headers=auth_headers)
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


class TestAuthEndpoints:
    def test_login_with_valid_credentials(self, client):
        """Login should work with valid credentials."""
        with patch.dict(os.environ, {"ADMIN_API_KEY": TEST_ADMIN_API_KEY}):
            # First create a user via admin API
            client.post(
                "/api/admin/users",
                json={
                    "name": "Login User",
                    "email": "login@example.com",
                    "password": "password123",
                },
                headers={"X-Admin-Api-Key": TEST_ADMIN_API_KEY},
            )

            # Then login
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "login@example.com",
                    "password": "password123",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["user"]["email"] == "login@example.com"

    def test_login_with_invalid_credentials(self, client):
        """Login should fail with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401


class TestNoteEndpoints:
    def test_get_note(self, client, auth_headers):
        """Get the shared household note."""
        response = client.get("/api/notes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "content" in data
        assert "updated_at" in data

    def test_update_note(self, client, auth_headers):
        """Update the shared household note."""
        response = client.put(
            "/api/notes",
            json={"content": "Shopping list:\n- Milk\n- Bread"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Shopping list:\n- Milk\n- Bread"
        assert "updated_at" in data

    def test_note_persists_after_update(self, client, auth_headers):
        """Verify that note content persists after update."""
        # Update note
        client.put(
            "/api/notes",
            json={"content": "Persistent content"},
            headers=auth_headers,
        )

        # Get note and verify content
        response = client.get("/api/notes", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["content"] == "Persistent content"

    def test_note_can_be_emptied(self, client, auth_headers):
        """Verify that note can be set to empty string."""
        # Set some content first
        client.put(
            "/api/notes",
            json={"content": "Some content"},
            headers=auth_headers,
        )

        # Clear the note
        response = client.put(
            "/api/notes",
            json={"content": ""},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["content"] == ""

    def test_note_requires_authentication(self, client):
        """Note endpoints should require authentication."""
        # GET without auth
        response = client.get("/api/notes")
        assert response.status_code == 401

        # PUT without auth
        response = client.put("/api/notes", json={"content": "test"})
        assert response.status_code == 401


class TestAdminEndpoints:
    def test_create_user_without_api_key(self, client):
        """Creating user without API key should fail."""
        response = client.post(
            "/api/admin/users",
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 422  # Missing required header

    def test_create_user_with_invalid_api_key(self, client):
        """Creating user with invalid API key should fail."""
        with patch.dict(os.environ, {"ADMIN_API_KEY": TEST_ADMIN_API_KEY}):
            response = client.post(
                "/api/admin/users",
                json={
                    "name": "New User",
                    "email": "newuser@example.com",
                    "password": "password123",
                },
                headers={"X-Admin-Api-Key": "wrong-key"},
            )
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid admin API key"

    def test_create_user_with_valid_api_key(self, client):
        """Creating user with valid API key should succeed."""
        with patch.dict(os.environ, {"ADMIN_API_KEY": TEST_ADMIN_API_KEY}):
            response = client.post(
                "/api/admin/users",
                json={
                    "name": "Admin Created User",
                    "email": "admin-created@example.com",
                    "password": "password123",
                },
                headers={"X-Admin-Api-Key": TEST_ADMIN_API_KEY},
            )
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Admin Created User"
            assert data["email"] == "admin-created@example.com"
            assert "id" in data
            # Should not return password_hash
            assert "password_hash" not in data

    def test_create_user_with_duplicate_email(self, client):
        """Creating user with duplicate email should fail."""
        with patch.dict(os.environ, {"ADMIN_API_KEY": TEST_ADMIN_API_KEY}):
            # Create first user
            client.post(
                "/api/admin/users",
                json={
                    "name": "First User",
                    "email": "duplicate@example.com",
                    "password": "password123",
                },
                headers={"X-Admin-Api-Key": TEST_ADMIN_API_KEY},
            )

            # Try to create second user with same email
            response = client.post(
                "/api/admin/users",
                json={
                    "name": "Second User",
                    "email": "duplicate@example.com",
                    "password": "password123",
                },
                headers={"X-Admin-Api-Key": TEST_ADMIN_API_KEY},
            )
            assert response.status_code == 400

    def test_create_user_without_configured_api_key(self, client):
        """Creating user when ADMIN_API_KEY is not configured should fail."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove ADMIN_API_KEY from environment
            os.environ.pop("ADMIN_API_KEY", None)
            response = client.post(
                "/api/admin/users",
                json={
                    "name": "New User",
                    "email": "newuser@example.com",
                    "password": "password123",
                },
                headers={"X-Admin-Api-Key": "any-key"},
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "Admin API key not configured"
