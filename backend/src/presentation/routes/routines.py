from fastapi import APIRouter, HTTPException, Depends

from src.domain import HouseholdMember
from src.application import GetAllRoutines, CreateRoutineBatch, UpdateRoutineAssignment, DeleteRoutine
from src.infrastructure import get_database, SQLiteWeeklyRoutineRepository
from ..schemas import RoutineCreateRequest, RoutineAssignRequest, RoutineResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/routines", tags=["routines"])


def get_routine_repo():
    db = get_database()
    return SQLiteWeeklyRoutineRepository(db)


@router.get("", response_model=list[RoutineResponse])
def list_routines(
    current_user: HouseholdMember = Depends(get_current_user),
    routine_repo: SQLiteWeeklyRoutineRepository = Depends(get_routine_repo),
):
    use_case = GetAllRoutines(routine_repo)
    routines = use_case.execute()
    return [
        RoutineResponse(
            id=r.id,
            name=r.name,
            day_of_week=r.day_of_week,
            time_of_day=r.time_of_day,
            assigned_to_id=r.assigned_to_id,
            sort_order=r.sort_order,
        )
        for r in routines
    ]


@router.post("", response_model=list[RoutineResponse], status_code=201)
def create_routines(
    request: RoutineCreateRequest,
    current_user: HouseholdMember = Depends(get_current_user),
    routine_repo: SQLiteWeeklyRoutineRepository = Depends(get_routine_repo),
):
    use_case = CreateRoutineBatch(routine_repo)
    routines = use_case.execute(
        name=request.name,
        days_of_week=request.days_of_week,
        time_of_day=request.time_of_day,
        assigned_to_id=request.assigned_to_id,
    )
    return [
        RoutineResponse(
            id=r.id,
            name=r.name,
            day_of_week=r.day_of_week,
            time_of_day=r.time_of_day,
            assigned_to_id=r.assigned_to_id,
            sort_order=r.sort_order,
        )
        for r in routines
    ]


@router.put("/{routine_id}/assign", response_model=RoutineResponse)
def assign_routine(
    routine_id: int,
    request: RoutineAssignRequest,
    current_user: HouseholdMember = Depends(get_current_user),
    routine_repo: SQLiteWeeklyRoutineRepository = Depends(get_routine_repo),
):
    use_case = UpdateRoutineAssignment(routine_repo)
    routine = use_case.execute(routine_id=routine_id, assigned_to_id=request.assigned_to_id)
    if routine is None:
        raise HTTPException(status_code=404, detail="Routine not found")
    return RoutineResponse(
        id=routine.id,
        name=routine.name,
        day_of_week=routine.day_of_week,
        time_of_day=routine.time_of_day,
        assigned_to_id=routine.assigned_to_id,
        sort_order=routine.sort_order,
    )


@router.delete("/{routine_id}", status_code=204)
def delete_routine(
    routine_id: int,
    current_user: HouseholdMember = Depends(get_current_user),
    routine_repo: SQLiteWeeklyRoutineRepository = Depends(get_routine_repo),
):
    use_case = DeleteRoutine(routine_repo)
    use_case.execute(routine_id=routine_id)
