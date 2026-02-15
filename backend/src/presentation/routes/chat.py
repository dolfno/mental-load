from fastapi import APIRouter, Depends

from src.domain import HouseholdMember
from src.application import SaveChatMessage, GetChatHistory, ClearChatHistory
from src.infrastructure import (
    get_database,
    SQLiteTaskRepository,
    SQLiteMemberRepository,
    SQLiteCompletionRepository,
    SQLiteNoteRepository,
    SQLiteChatMessageRepository,
)
from src.infrastructure.llm_service import LLMService
from ..schemas import ChatSendRequest, ChatMessageResponse, ChatResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_chat_repo():
    db = get_database()
    return SQLiteChatMessageRepository(db)


def get_llm_service():
    db = get_database()
    return LLMService(
        task_repo=SQLiteTaskRepository(db),
        member_repo=SQLiteMemberRepository(db),
        completion_repo=SQLiteCompletionRepository(db),
        note_repo=SQLiteNoteRepository(db),
    )


@router.post("", response_model=ChatResponse)
def send_message(
    request: ChatSendRequest,
    current_user: HouseholdMember = Depends(get_current_user),
    chat_repo: SQLiteChatMessageRepository = Depends(get_chat_repo),
    llm_service: LLMService = Depends(get_llm_service),
):
    save_use_case = SaveChatMessage(chat_repo)
    history_use_case = GetChatHistory(chat_repo)

    # Save user message
    user_msg = save_use_case.execute(
        user_id=current_user.id,
        role="user",
        content=request.message,
    )

    # Build conversation history for LLM
    history = history_use_case.execute(user_id=current_user.id, limit=50)
    messages = [{"role": msg.role, "content": msg.content} for msg in history]

    # Get LLM response
    assistant_content = llm_service.chat(messages)

    # Save assistant response
    assistant_msg = save_use_case.execute(
        user_id=current_user.id,
        role="assistant",
        content=assistant_content,
    )

    return ChatResponse(
        user_message=ChatMessageResponse(
            id=user_msg.id,
            role=user_msg.role,
            content=user_msg.content,
            created_at=user_msg.created_at,
        ),
        assistant_message=ChatMessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
        ),
    )


@router.get("/history", response_model=list[ChatMessageResponse])
def get_history(
    current_user: HouseholdMember = Depends(get_current_user),
    chat_repo: SQLiteChatMessageRepository = Depends(get_chat_repo),
):
    use_case = GetChatHistory(chat_repo)
    messages = use_case.execute(user_id=current_user.id)
    return [
        ChatMessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


@router.delete("/history", status_code=204)
def clear_history(
    current_user: HouseholdMember = Depends(get_current_user),
    chat_repo: SQLiteChatMessageRepository = Depends(get_chat_repo),
):
    use_case = ClearChatHistory(chat_repo)
    use_case.execute(user_id=current_user.id)
