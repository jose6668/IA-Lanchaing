import base64
import hashlib
import hmac
import re
import secrets
import sqlite3
from pathlib import Path


USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 600_000


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
                (clean_name, clean_username, self._hash_password(clean_password)),
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
                SELECT id, name, username, password
                FROM users
                WHERE username = ?
                """,
                (clean_username,),
            ).fetchone()

        if not row or not self._verify_password(clean_password, row[3]):
            return False, None, "Usuario o contrasena incorrectos."

        # Preserve existing local accounts, upgrading their legacy plaintext
        # password the first time they sign in. Fresh production databases
        # store only hashes from the first registration.
        if not row[3].startswith(f"{PASSWORD_HASH_ALGORITHM}$"):
            with self._connect() as connection:
                connection.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (self._hash_password(clean_password), row[0]),
                )

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

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
        )
        encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
        encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return (
            f"{PASSWORD_HASH_ALGORITHM}${PASSWORD_HASH_ITERATIONS}"
            f"${encoded_salt}${encoded_digest}"
        )

    @staticmethod
    def _verify_password(password: str, stored_value: str) -> bool:
        if not stored_value.startswith(f"{PASSWORD_HASH_ALGORITHM}$"):
            # Legacy local databases stored plain text. Compare in constant
            # time and re-hash only after successful authentication.
            return hmac.compare_digest(
                password.encode("utf-8"), stored_value.encode("utf-8")
            )

        try:
            algorithm, iteration_text, salt_text, digest_text = stored_value.split("$", 3)
            iterations = int(iteration_text)
            if algorithm != PASSWORD_HASH_ALGORITHM or not 100_000 <= iterations <= 2_000_000:
                return False
            salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
            expected = base64.urlsafe_b64decode(digest_text + "=" * (-len(digest_text) % 4))
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, iterations
            )
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(actual, expected)
