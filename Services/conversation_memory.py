import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Sequence

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict


class SQLiteLimitedChatMessageHistory(BaseChatMessageHistory):
    """Historial persistente por sesion con limite maximo de mensajes."""

    def __init__(
        self,
        session_id: str,
        db_path: Path,
        max_messages: int,
    ) -> None:
        self.session_id = session_id
        self.db_path = db_path
        self.max_messages = max_messages
        self._lock = Lock()
        self._ensure_database()

    @property
    def messages(self) -> list[BaseMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT message
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (self.session_id,),
            ).fetchall()

        serialized_messages = [json.loads(row[0]) for row in rows]
        return messages_from_dict(serialized_messages)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        if not messages:
            return

        serialized_messages = messages_to_dict(list(messages))

        with self._lock:
            with self._connect() as connection:
                connection.executemany(
                    """
                    INSERT INTO conversation_messages (session_id, message)
                    VALUES (?, ?)
                    """,
                    [
                        (
                            self.session_id,
                            json.dumps(message, ensure_ascii=False),
                        )
                        for message in serialized_messages
                    ],
                )
                self._trim_session_messages(connection)

    def clear(self) -> None:
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    DELETE FROM conversation_messages
                    WHERE session_id = ?
                    """,
                    (self.session_id,),
                )

    def _ensure_database(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversation_session_id
                ON conversation_messages(session_id, id)
                """
            )

    def _trim_session_messages(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            DELETE FROM conversation_messages
            WHERE session_id = ?
            AND id NOT IN (
                SELECT id
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            """,
            (
                self.session_id,
                self.session_id,
                self.max_messages,
            ),
        )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)


def get_recent_messages_for_ui(
    session_id: str,
    db_path: Path,
    max_messages: int,
) -> list[dict[str, str]]:
    history = SQLiteLimitedChatMessageHistory(
        session_id=session_id,
        db_path=db_path,
        max_messages=max_messages,
    )

    ui_messages = []

    for message in history.messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            continue

        ui_messages.append(
            {
                "role": role,
                "content": str(message.content),
            }
        )

    return ui_messages
