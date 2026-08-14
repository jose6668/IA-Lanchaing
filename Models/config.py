from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DOCS_DIR = BASE_DIR / "docs"

DIAGNOSTIC_PDF_PATH = (
    DOCS_DIR
    / "Reporte_Ejecutivo_Encuesta_Programacion.pdf"
)

DIAGNOSTIC_CHROMA_PATH = (
    BASE_DIR
    / "chroma_diagnostico"
)

DIAGNOSTIC_COLLECTION_NAME = "student_diagnostic"

MODEL_NAME = "gpt-4o-mini"
EMBEDDINGS_MODEL = "text-embedding-3-small"

TEMPERATURE = 0.3

RETRIEVAL_K = 2