import sqlite3
from pathlib import Path
from uuid import uuid4


class ChatManager:
    """Gestiona multiples chats asociados a usuarios locales."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_database()

    def create_chat(
        self,
        username: str,
        first_message: str = "",
    ) -> dict[str, str]:
        chat_id = uuid4().hex
        title = self._build_title(first_message)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chats (chat_id, username, title, message_count)
                VALUES (?, ?, ?, 0)
                """,
                (chat_id, username, title),
            )

        return {
            "chat_id": chat_id,
            "username": username,
            "title": title,
            "message_count": "0",
        }

    def list_chats(self, username: str) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chat_id, username, title, created_at, updated_at, message_count
                FROM chats
                WHERE username = ?
                ORDER BY updated_at DESC, id DESC
                """,
                (username,),
            ).fetchall()

        return [
            {
                "chat_id": row[0],
                "username": row[1],
                "title": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "message_count": str(row[5]),
            }
            for row in rows
        ]

    def get_chat(self, username: str, chat_id: str) -> dict[str, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT chat_id, username, title, created_at, updated_at, message_count
                FROM chats
                WHERE username = ?
                AND chat_id = ?
                """,
                (username, chat_id),
            ).fetchone()

        if not row:
            return None

        return {
            "chat_id": row[0],
            "username": row[1],
            "title": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "message_count": str(row[5]),
        }

    def delete_chat(self, username: str, chat_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM chats
                WHERE username = ?
                AND chat_id = ?
                """,
                (username, chat_id),
            )

    def touch_chat(
        self,
        username: str,
        chat_id: str,
        first_message: str = "",
    ) -> None:
        chat = self.get_chat(username, chat_id)
        title_update = ""
        params: tuple

        if chat and chat["title"] == "Nuevo chat" and first_message:
            title_update = ", title = ?"
            params = (
                self._build_title(first_message),
                username,
                chat_id,
            )
        else:
            params = (
                username,
                chat_id,
            )

        with self._connect() as connection:
            connection.execute(
                f"""
                UPDATE chats
                SET updated_at = CURRENT_TIMESTAMP,
                    message_count = message_count + 2
                    {title_update}
                WHERE username = ?
                AND chat_id = ?
                """,
                params,
            )

    def build_session_id(self, username: str, chat_id: str) -> str:
        return f"user_{username}_chat_{chat_id}"

    def _build_title(self, first_message: str) -> str:
        clean_message = " ".join(first_message.strip().split())

        if not clean_message:
            return "Nuevo chat"

        return (
            clean_message[:37] + "..."
            if len(clean_message) > 40
            else clean_message
        )

    def _ensure_database(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chats_username
                ON chats(username, updated_at)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)
