"""
History feature - common types.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SavedPrompt:
    id: int
    technique: str
    task: str
    prompt: str
    tags: list[str]
    is_favorite: bool
    created_at: datetime

    @classmethod
    def from_row(cls, row: tuple) -> "SavedPrompt":
        return cls(
            id=row[0],
            technique=row[1],
            task=row[2],
            prompt=row[3],
            tags=row[4].split(",") if row[4] else [],
            is_favorite=bool(row[5]),
            created_at=datetime.fromisoformat(row[6])
        )
