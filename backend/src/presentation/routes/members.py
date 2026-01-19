from fastapi import APIRouter, HTTPException, Depends

from src.domain import HouseholdMember
from src.application import CreateMember, GetAllMembers, DeleteMember
from src.infrastructure import get_database, SQLiteMemberRepository
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
    current_user: HouseholdMember = Depends(get_current_user),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    use_case = DeleteMember(member_repo)
    success = use_case.execute(member_id=member_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
