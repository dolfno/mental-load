from abc import ABC, abstractmethod
from datetime import date

from src.domain import Task, HouseholdMember, TaskCompletion


class TaskRepository(ABC):
    @abstractmethod
    def get_all(self, active_only: bool = True) -> list[Task]:
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task | None:
        pass

    @abstractmethod
    def get_by_due_date_range(self, start: date, end: date) -> list[Task]:
        pass

    @abstractmethod
    def save(self, task: Task) -> Task:
        pass

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        pass


class MemberRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[HouseholdMember]:
        pass

    @abstractmethod
    def get_by_id(self, member_id: int) -> HouseholdMember | None:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> HouseholdMember | None:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> HouseholdMember | None:
        pass

    @abstractmethod
    def save(self, member: HouseholdMember) -> HouseholdMember:
        pass

    @abstractmethod
    def delete(self, member_id: int) -> bool:
        pass


class CompletionRepository(ABC):
    @abstractmethod
    def get_all(self, limit: int | None = None) -> list[TaskCompletion]:
        pass

    @abstractmethod
    def get_by_task(self, task_id: int) -> list[TaskCompletion]:
        pass

    @abstractmethod
    def get_by_member(self, member_id: int) -> list[TaskCompletion]:
        pass

    @abstractmethod
    def save(self, completion: TaskCompletion) -> TaskCompletion:
        pass
