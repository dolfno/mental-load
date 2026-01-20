from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from src.domain import HouseholdMember
from src.application import CreateMember, GetAllMembers, DeleteMember
from src.infrastructure import get_database, SQLiteMemberRepository, SQLiteCompletionRepository, SQLiteTaskRepository
from ..schemas import MemberCreateRequest, MemberResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/members", tags=["members"])


def get_member_repo():
    db = get_database()
    return SQLiteMemberRepository(db)


@router.get("", response_model=list[MemberResponse])
def list_members(
    current_user: HouseholdMember = Depends(get_current_user),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    use_case = GetAllMembers(member_repo)
    members = use_case.execute()
    return [MemberResponse(id=m.id, name=m.name) for m in members]


@router.post("", response_model=MemberResponse, status_code=201)
def create_member(
    request: MemberCreateRequest,
    current_user: HouseholdMember = Depends(get_current_user),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    use_case = CreateMember(member_repo)
    member = use_case.execute(name=request.name)
    return MemberResponse(id=member.id, name=member.name)


@router.delete("/{member_id}", status_code=204)
def delete_member(
    member_id: int,
    force: bool = Query(False, description="Force deletion by anonymizing history"),
    current_user: HouseholdMember = Depends(get_current_user),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    db = get_database()
    completion_repo = SQLiteCompletionRepository(db)
    task_repo = SQLiteTaskRepository(db)

    use_case = DeleteMember(member_repo, completion_repo, task_repo)
    result = use_case.execute(member_id=member_id, force=force)

    if result.requires_confirmation and result.reference_info:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Member has associated data. Use force=true to delete and anonymize history.",
                "completion_count": result.reference_info.completion_count,
                "assignment_count": result.reference_info.assignment_count,
            },
        )
