from src.domain import WeeklyRoutine, TimeOfDay
from .interfaces import WeeklyRoutineRepository


class GetAllRoutines:
    def __init__(self, routine_repo: WeeklyRoutineRepository):
        self.routine_repo = routine_repo

    def execute(self) -> list[WeeklyRoutine]:
        return self.routine_repo.get_all()


class CreateRoutineBatch:
    def __init__(self, routine_repo: WeeklyRoutineRepository):
        self.routine_repo = routine_repo

    def execute(
        self,
        name: str,
        days_of_week: list[int],
        time_of_day: TimeOfDay,
        assigned_to_id: int | None = None,
    ) -> list[WeeklyRoutine]:
        routines = []
        for day in days_of_week:
            routine = WeeklyRoutine(
                id=None,
                name=name,
                day_of_week=day,
                time_of_day=time_of_day,
                assigned_to_id=assigned_to_id,
            )
            saved = self.routine_repo.save(routine)
            routines.append(saved)
        return routines


class UpdateRoutineAssignment:
    def __init__(self, routine_repo: WeeklyRoutineRepository):
        self.routine_repo = routine_repo

    def execute(self, routine_id: int, assigned_to_id: int | None) -> WeeklyRoutine | None:
        routine = self.routine_repo.get_by_id(routine_id)
        if routine is None:
            return None
        routine.assigned_to_id = assigned_to_id
        return self.routine_repo.save(routine)


class DeleteRoutine:
    def __init__(self, routine_repo: WeeklyRoutineRepository):
        self.routine_repo = routine_repo

    def execute(self, routine_id: int) -> bool:
        return self.routine_repo.delete(routine_id)
