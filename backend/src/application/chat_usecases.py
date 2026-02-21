from datetime import datetime

from src.domain import ChatMessage
from .interfaces import ChatMessageRepository


class GetChatHistory:
    def __init__(self, chat_repo: ChatMessageRepository):
        self.chat_repo = chat_repo

    def execute(self, user_id: int, limit: int = 50) -> list[ChatMessage]:
        return self.chat_repo.get_by_user(user_id, limit=limit)


class SaveChatMessage:
    def __init__(self, chat_repo: ChatMessageRepository):
        self.chat_repo = chat_repo

    def execute(self, user_id: int, role: str, content: str) -> ChatMessage:
        message = ChatMessage(
            id=None,
            user_id=user_id,
            role=role,
            content=content,
            created_at=datetime.now(),
        )
        return self.chat_repo.save(message)


class ClearChatHistory:
    def __init__(self, chat_repo: ChatMessageRepository):
        self.chat_repo = chat_repo

    def execute(self, user_id: int) -> None:
        self.chat_repo.delete_by_user(user_id)
