"""Unit tests for chat use cases with mocked repositories."""

from datetime import datetime
from unittest.mock import MagicMock

from src.domain import ChatMessage
from src.application import GetChatHistory, SaveChatMessage, ClearChatHistory


class TestGetChatHistory:
    def test_returns_messages_for_user(self):
        mock_repo = MagicMock()
        mock_repo.get_by_user.return_value = [
            ChatMessage(id=1, user_id=1, role="user", content="Hello", created_at=datetime(2026, 1, 1)),
            ChatMessage(id=2, user_id=1, role="assistant", content="Hi!", created_at=datetime(2026, 1, 1)),
        ]

        use_case = GetChatHistory(mock_repo)
        result = use_case.execute(user_id=1)

        assert len(result) == 2
        assert result[0].role == "user"
        assert result[1].role == "assistant"
        mock_repo.get_by_user.assert_called_once_with(1, limit=50)

    def test_returns_empty_list_for_no_messages(self):
        mock_repo = MagicMock()
        mock_repo.get_by_user.return_value = []

        use_case = GetChatHistory(mock_repo)
        result = use_case.execute(user_id=1)

        assert result == []

    def test_respects_limit_parameter(self):
        mock_repo = MagicMock()
        mock_repo.get_by_user.return_value = []

        use_case = GetChatHistory(mock_repo)
        use_case.execute(user_id=1, limit=10)

        mock_repo.get_by_user.assert_called_once_with(1, limit=10)


class TestSaveChatMessage:
    def test_saves_user_message(self):
        mock_repo = MagicMock()
        mock_repo.save.return_value = ChatMessage(
            id=1, user_id=1, role="user", content="Hello", created_at=datetime(2026, 1, 1)
        )

        use_case = SaveChatMessage(mock_repo)
        result = use_case.execute(user_id=1, role="user", content="Hello")

        assert result.id == 1
        assert result.role == "user"
        assert result.content == "Hello"
        mock_repo.save.assert_called_once()

    def test_saves_assistant_message(self):
        mock_repo = MagicMock()
        mock_repo.save.return_value = ChatMessage(
            id=2, user_id=1, role="assistant", content="Hi there!", created_at=datetime(2026, 1, 1)
        )

        use_case = SaveChatMessage(mock_repo)
        result = use_case.execute(user_id=1, role="assistant", content="Hi there!")

        assert result.id == 2
        assert result.role == "assistant"
        assert result.content == "Hi there!"


class TestClearChatHistory:
    def test_deletes_messages_for_user(self):
        mock_repo = MagicMock()

        use_case = ClearChatHistory(mock_repo)
        use_case.execute(user_id=1)

        mock_repo.delete_by_user.assert_called_once_with(1)
