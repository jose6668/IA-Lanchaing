"""Environment configuration. Existing shell variables take precedence over .env."""
import math
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=False, interpolate=False)


class ConfigurationError(ValueError):
    """Invalid configuration; messages contain names, never secret values."""


def integer(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        raise ConfigurationError(f'{name} debe ser un número entero.') from None
    if not minimum <= value <= maximum:
        raise ConfigurationError(f'{name} debe estar entre {minimum} y {maximum}.')
    return value


APP_ENV = os.environ.get('APP_ENV', 'development').strip().lower()
if APP_ENV not in {'development', 'production'}:
    raise ConfigurationError('APP_ENV debe ser development o production.')

MODEL_NAME = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini').strip()
if not MODEL_NAME:
    raise ConfigurationError('OPENAI_MODEL no puede estar vacío.')
try:
    TEMPERATURE = float(os.environ.get('MODEL_TEMPERATURE', '0.3'))
except ValueError:
    raise ConfigurationError('MODEL_TEMPERATURE debe ser un número.') from None
if not math.isfinite(TEMPERATURE) or not 0 <= TEMPERATURE <= 2:
    raise ConfigurationError('MODEL_TEMPERATURE debe estar entre 0 y 2.')

# Keep the historical development path; production must explicitly select storage.
_db_path = os.environ.get('MEMORY_DB_PATH', '').strip()
if APP_ENV == 'production' and (not _db_path or not Path(_db_path).is_absolute()):
    raise ConfigurationError('En producción, MEMORY_DB_PATH debe ser una ruta absoluta en almacenamiento persistente.')
MEMORY_DB_PATH = Path(_db_path).expanduser() if _db_path else BASE_DIR / 'conversation_memory.sqlite'
if not MEMORY_DB_PATH.is_absolute():
    MEMORY_DB_PATH = BASE_DIR / MEMORY_DB_PATH

MAX_HISTORY_MESSAGES = integer('MAX_HISTORY_MESSAGES', 20, 2, 100)
MODEL_TIMEOUT_SECONDS = integer('MODEL_TIMEOUT_SECONDS', 60, 5, 300)
MODEL_MAX_RETRIES = integer('MODEL_MAX_RETRIES', 2, 0, 5)
MODEL_MAX_TOKENS = integer('MODEL_MAX_TOKENS', 1500, 64, 8192)


def validate_api_key() -> None:
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key or key in {'replace-me', 'your-api-key', 'sk-example'}:
        raise ConfigurationError('Configura OPENAI_API_KEY en el entorno o en el archivo privado .env.')
