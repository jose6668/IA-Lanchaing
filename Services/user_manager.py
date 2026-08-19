import re
import sqlite3
from pathlib import Path


USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")


class UserManager:
    """Gestiona usuarios locales del asistente educativo."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_database()

    def create_user(
        self,
        name: str,
        username: str,
        password: str,
    ) -> tuple[bool, str]:
        clean_name = name.strip()
        clean_username = username.strip().lower()
        clean_password = password.strip()

        validation_error = self.validate_user_data(
            name=clean_name,
            username=clean_username,
            password=clean_password,
        )
        if validation_error:
            return False, validation_error

        if self.user_exists(clean_username):
            return False, "El nombre de usuario ya existe."

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (name, username, password)
                VALUES (?, ?, ?)
                """,
                (clean_name, clean_username, clean_password),
            )

        return True, "Usuario creado correctamente."

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> tuple[bool, dict[str, str] | None, str]:
        clean_username = username.strip().lower()
        clean_password = password.strip()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, username
                FROM users
                WHERE username = ?
                AND password = ?
                """,
                (clean_username, clean_password),
            ).fetchone()

        if not row:
            return False, None, "Usuario o contrasena incorrectos."

        user = {
            "id": str(row[0]),
            "name": row[1],
            "username": row[2],
        }
        return True, user, "Inicio de sesion correcto."

    def user_exists(self, username: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM users
                WHERE username = ?
                """,
                (username.strip().lower(),),
            ).fetchone()

        return row is not None

    def validate_user_data(
        self,
        name: str,
        username: str,
        password: str,
    ) -> str | None:
        if not name:
            return "El nombre no puede estar vacio."

        if not username:
            return "El nombre de usuario no puede estar vacio."

        if not USERNAME_PATTERN.match(username):
            return (
                "El nombre de usuario debe tener entre 3 y 30 caracteres "
                "y usar solo letras, numeros, guion o guion bajo."
            )

        if not password:
            return "La contrasena no puede estar vacia."

        return None

    def _ensure_database(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)
