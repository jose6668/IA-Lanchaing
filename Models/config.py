from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_NAME = "gpt-4o-mini"

TEMPERATURE = 0.3

MEMORY_DB_PATH = BASE_DIR / "conversation_memory.sqlite"

MAX_HISTORY_MESSAGES = 20
