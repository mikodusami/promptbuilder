"""
History feature - service for managing prompt history.
"""

import sqlite3
from typing import Optional

from ...platform.storage import BaseStorage
from .common import SavedPrompt


class HistoryService(BaseStorage):
    """Manage prompt history with SQLite storage."""

    def __init__(self, db_path: Optional[str] = None):
        super().__init__("history.db", db_path)

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    technique TEXT NOT NULL,
                    task TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    tags TEXT DEFAULT '',
                    is_favorite INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_technique ON prompts(technique)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_favorite ON prompts(is_favorite)")
            conn.commit()

    def save(self, technique: str, task: str, prompt: str, tags: list[str] = None) -> int:
        """Save a prompt and return its ID."""
        tags_str = ",".join(tags) if tags else ""
        return self.execute_write(
            "INSERT INTO prompts (technique, task, prompt, tags) VALUES (?, ?, ?, ?)",
            (technique, task, prompt, tags_str)
        )

    def get(self, prompt_id: int) -> Optional[SavedPrompt]:
        """Get a prompt by ID."""
        rows = self.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        return SavedPrompt.from_row(rows[0]) if rows else None

    def list_recent(self, limit: int = 10) -> list[SavedPrompt]:
        """List recent prompts."""
        rows = self.execute(
            "SELECT * FROM prompts ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [SavedPrompt.from_row(r) for r in rows]

    def list_favorites(self) -> list[SavedPrompt]:
        """List favorite prompts."""
        rows = self.execute(
            "SELECT * FROM prompts WHERE is_favorite = 1 ORDER BY created_at DESC"
        )
        return [SavedPrompt.from_row(r) for r in rows]

    def search(self, query: str) -> list[SavedPrompt]:
        """Search prompts by task or tags."""
        rows = self.execute(
            "SELECT * FROM prompts WHERE task LIKE ? OR tags LIKE ? ORDER BY created_at DESC",
            (f"%{query}%", f"%{query}%")
        )
        return [SavedPrompt.from_row(r) for r in rows]

    def toggle_favorite(self, prompt_id: int) -> bool:
        """Toggle favorite status, returns new status."""
        rows = self.execute("SELECT is_favorite FROM prompts WHERE id = ?", (prompt_id,))
        if not rows:
            return False
        new_status = 0 if rows[0][0] else 1
        self.execute_write("UPDATE prompts SET is_favorite = ? WHERE id = ?", (new_status, prompt_id))
        return bool(new_status)

    def delete(self, prompt_id: int) -> bool:
        """Delete a prompt."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
            conn.commit()
            return cursor.rowcount > 0
