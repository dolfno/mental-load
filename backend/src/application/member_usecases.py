from src.domain import HouseholdMember, TaskCompletion
from .interfaces import MemberRepository, CompletionRepository


class CreateMember:
    def __init__(self, member_repo: MemberRepository):
        self.member_repo = member_repo

    def execute(self, name: str) -> HouseholdMember:
        # Check if member already exists
        existing = self.member_repo.get_by_name(name)
        if existing:
            return existing

        member = HouseholdMember(id=None, name=name)
        return self.member_repo.save(member)


class GetAllMembers:
    def __init__(self, member_repo: MemberRepository):
        self.member_repo = member_repo

    def execute(self) -> list[HouseholdMember]:
        return self.member_repo.get_all()


class DeleteMember:
    def __init__(self, member_repo: MemberRepository):
        self.member_repo = member_repo

    def execute(self, member_id: int) -> bool:
        return self.member_repo.delete(member_id)


class GetCompletionHistory:
    def __init__(self, completion_repo: CompletionRepository):
        self.completion_repo = completion_repo

    def execute(self, limit: int | None = None) -> list[TaskCompletion]:
        return self.completion_repo.get_all(limit=limit)
