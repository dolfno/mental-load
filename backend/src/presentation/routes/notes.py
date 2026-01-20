from fastapi import APIRouter, Depends, HTTPException

from src.domain import HouseholdMember
from src.application import GetNote, UpdateNote
from src.infrastructure import get_database, SQLiteNoteRepository
from ..schemas import NoteUpdateRequest, NoteResponse
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/notes", tags=["notes"])


def get_note_repo():
    db = get_database()
    return SQLiteNoteRepository(db)


@router.get("", response_model=NoteResponse)
def get_note(
    current_user: HouseholdMember = Depends(get_current_user),
    note_repo: SQLiteNoteRepository = Depends(get_note_repo),
):
    use_case = GetNote(note_repo)
    note = use_case.execute()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(
        id=note.id,
        content=note.content,
        updated_at=note.updated_at,
    )


@router.put("", response_model=NoteResponse)
def update_note(
    request: NoteUpdateRequest,
    current_user: HouseholdMember = Depends(get_current_user),
    note_repo: SQLiteNoteRepository = Depends(get_note_repo),
):
    use_case = UpdateNote(note_repo)
    note = use_case.execute(content=request.content)
    return NoteResponse(
        id=note.id,
        content=note.content,
        updated_at=note.updated_at,
    )
