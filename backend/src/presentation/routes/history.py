from fastapi import APIRouter, Depends

from src.application import GetCompletionHistory
from src.infrastructure import (
    get_database,
    SQLiteCompletionRepository,
    SQLiteTaskRepository,
    SQLiteMemberRepository,
)
from ..schemas import TaskCompletionResponse

router = APIRouter(prefix="/api/history", tags=["history"])


def get_completion_repo():
    db = get_database()
    return SQLiteCompletionRepository(db)


def get_task_repo():
    db = get_database()
    return SQLiteTaskRepository(db)


def get_member_repo():
    db = get_database()
    return SQLiteMemberRepository(db)


@router.get("", response_model=list[TaskCompletionResponse])
def list_history(
    limit: int | None = 100,
    completion_repo: SQLiteCompletionRepository = Depends(get_completion_repo),
    task_repo: SQLiteTaskRepository = Depends(get_task_repo),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    use_case = GetCompletionHistory(completion_repo)
    completions = use_case.execute(limit=limit)

    # Enrich with task and member names
    result = []
    for completion in completions:
        task = task_repo.get_by_id(completion.task_id)
        member = member_repo.get_by_id(completion.completed_by_id)

        result.append(
            TaskCompletionResponse(
                id=completion.id,
                task_id=completion.task_id,
                task_name=task.name if task else None,
                completed_at=completion.completed_at,
                completed_by_id=completion.completed_by_id,
                completed_by_name=member.name if member else None,
            )
        )

    return result
