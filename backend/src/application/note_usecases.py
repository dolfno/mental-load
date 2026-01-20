from datetime import datetime

from src.domain import Note
from .interfaces import NoteRepository


class GetNote:
    def __init__(self, note_repo: NoteRepository):
        self.note_repo = note_repo

    def execute(self) -> Note | None:
        return self.note_repo.get()


class UpdateNote:
    def __init__(self, note_repo: NoteRepository):
        self.note_repo = note_repo

    def execute(self, content: str) -> Note:
        note = self.note_repo.get()
        if note is None:
            note = Note(id=None, content=content, updated_at=datetime.now())
        else:
            note.content = content
            note.updated_at = datetime.now()
        return self.note_repo.save(note)
