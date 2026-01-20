from dataclasses import dataclass

from src.domain import HouseholdMember, TaskCompletion
from .interfaces import MemberRepository, CompletionRepository, TaskRepository


@dataclass
class MemberReferenceInfo:
    """Information about a member's references in the system."""
    completion_count: int
    assignment_count: int

    @property
    def has_references(self) -> bool:
        return self.completion_count > 0 or self.assignment_count > 0


@dataclass
class DeleteMemberResult:
    """Result of attempting to delete a member."""
    success: bool
    requires_confirmation: bool = False
    reference_info: MemberReferenceInfo | None = None


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
    def __init__(
        self,
        member_repo: MemberRepository,
        completion_repo: CompletionRepository | None = None,
        task_repo: TaskRepository | None = None,
    ):
        self.member_repo = member_repo
        self.completion_repo = completion_repo
        self.task_repo = task_repo

    def execute(self, member_id: int, force: bool = False) -> DeleteMemberResult:
        # Check for references if we have the repos
        completion_count = 0
        assignment_count = 0

        if self.completion_repo is not None and hasattr(self.completion_repo, 'count_by_member'):
            completion_count = self.completion_repo.count_by_member(member_id)

        if self.task_repo is not None and hasattr(self.task_repo, 'count_by_assigned_member'):
            assignment_count = self.task_repo.count_by_assigned_member(member_id)

        reference_info = MemberReferenceInfo(
            completion_count=completion_count,
            assignment_count=assignment_count,
        )

        # If there are references and force is not set, return conflict
        if reference_info.has_references and not force:
            return DeleteMemberResult(
                success=False,
                requires_confirmation=True,
                reference_info=reference_info,
            )

        # Clear references if force is set
        if force and reference_info.has_references:
            if self.completion_repo is not None and hasattr(self.completion_repo, 'clear_member_references'):
                self.completion_repo.clear_member_references(member_id)
            if self.task_repo is not None and hasattr(self.task_repo, 'clear_member_assignments'):
                self.task_repo.clear_member_assignments(member_id)

        # Delete the member
        self.member_repo.delete(member_id)
        return DeleteMemberResult(success=True)


class GetCompletionHistory:
    def __init__(self, completion_repo: CompletionRepository):
        self.completion_repo = completion_repo

    def execute(self, limit: int | None = None) -> list[TaskCompletion]:
        return self.completion_repo.get_all(limit=limit)
