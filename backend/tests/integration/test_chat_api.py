"""Integration tests for chat API endpoints."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

from src.infrastructure import Database, set_database
from src.presentation.main import app

TEST_ADMIN_API_KEY = "test-admin-api-key"


@pytest.fixture
def test_db():
    """Create a temporary test database with actual migrations."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    command.upgrade(alembic_cfg, "head")

    db = Database(path, use_turso=False)
    set_database(db)

    yield db

    set_database(None)
    os.unlink(path)


@pytest.fixture
def client(test_db):
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    with patch.dict(os.environ, {"ADMIN_API_KEY": TEST_ADMIN_API_KEY}):
        client.post(
            "/api/admin/users",
            json={"name": "Test User", "email": "test@example.com", "password": "testpassword123"},
            headers={"X-Admin-Api-Key": TEST_ADMIN_API_KEY},
        )
        login_response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


class TestChatEndpoints:
    def test_get_empty_history(self, client, auth_headers):
        response = client.get("/api/chat/history", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_send_message_without_llm_config(self, client, auth_headers):
        """When LLM is not configured, should still return a response."""
        with patch.dict(os.environ, {"LLM_API_KEY": ""}, clear=False):
            response = client.post(
                "/api/chat",
                json={"message": "Hello"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user_message"]["role"] == "user"
            assert data["user_message"]["content"] == "Hello"
            assert data["assistant_message"]["role"] == "assistant"
            # Should indicate AI is not configured
            assert "niet geconfigureerd" in data["assistant_message"]["content"].lower() or "not configured" in data["assistant_message"]["content"].lower()

    def test_send_message_with_mocked_llm(self, client, auth_headers):
        """Test chat with a mocked LLM service."""
        with patch("src.presentation.routes.chat.get_llm_service") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.chat.return_value = "I can help you with that!"
            mock_get_llm.return_value = mock_llm

            response = client.post(
                "/api/chat",
                json={"message": "What tasks are urgent?"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user_message"]["content"] == "What tasks are urgent?"
            assert data["assistant_message"]["content"] == "I can help you with that!"

    def test_chat_history_persists(self, client, auth_headers):
        """Messages should be persisted and retrievable."""
        with patch("src.presentation.routes.chat.get_llm_service") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.chat.return_value = "Response 1"
            mock_get_llm.return_value = mock_llm

            client.post(
                "/api/chat",
                json={"message": "Message 1"},
                headers=auth_headers,
            )

        # Fetch history
        response = client.get("/api/chat/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # user + assistant
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "Message 1"
        assert data[1]["role"] == "assistant"
        assert data[1]["content"] == "Response 1"

    def test_clear_history(self, client, auth_headers):
        """Clearing history should remove all messages."""
        with patch("src.presentation.routes.chat.get_llm_service") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.chat.return_value = "Hello!"
            mock_get_llm.return_value = mock_llm

            client.post(
                "/api/chat",
                json={"message": "Hi"},
                headers=auth_headers,
            )

        # Clear history
        response = client.delete("/api/chat/history", headers=auth_headers)
        assert response.status_code == 204

        # Verify history is empty
        response = client.get("/api/chat/history", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_chat_requires_authentication(self, client):
        response = client.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == 403

    def test_history_requires_authentication(self, client):
        response = client.get("/api/chat/history")
        assert response.status_code == 403
