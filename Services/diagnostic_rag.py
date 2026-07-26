import unicodedata
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from Models.config import *


# Todas estas palabras están escritas SIN tildes ni ñ porque
# las preguntas también serán normalizadas antes de compararlas.
DIAGNOSTIC_KEYWORDS = {
    "companero",
    "companeros",
    "clase",
    "estudiante",
    "estudiantes",
    "grupo",
    "encuesta",
    "diagnostico",
    "reporte",
    "documento",
    "pdf",
    "dificultad",
    "dificultades",
    "falencia",
    "falencias",
    "frustracion",
    "porcentaje",
    "porcentajes",
    "resultado",
    "resultados",
    "preferencia",
    "preferencias",
    "conocimiento",
    "conocimientos",
    "nivel",
    "niveles",
    "mayor dificultad",
    "principal dificultad",
    "problemas del grupo",
    "programacion en bachillerato",
}


SUMMARY_KEYWORDS = {
    "resumen",
    "resume",
    "resumir",
    "sintesis",
    "resumen completo",
    "resumen del documento",
    "resumen del pdf",
}


def normalize_text(text: str) -> str:
    """
    Convierte un texto a minúsculas, elimina tildes y transforma
    la letra ñ en n para facilitar las comparaciones.
    """

    lowercase_text = text.lower().strip()

    normalized_text = unicodedata.normalize(
        "NFD",
        lowercase_text,
    )

    return "".join(
        character
        for character in normalized_text
        if unicodedata.category(character) != "Mn"
    )


def is_diagnostic_question(question: str) -> bool:
    """
    Detecta si la consulta está relacionada con el diagnóstico,
    la encuesta, el grupo o el documento.
    """

    normalized_question = normalize_text(question)

    return any(
        keyword in normalized_question
        for keyword in DIAGNOSTIC_KEYWORDS
    )


def is_summary_question(question: str) -> bool:
    """Detecta solicitudes de resumen del documento."""

    normalized_question = normalize_text(question)

    return any(
        keyword in normalized_question
        for keyword in SUMMARY_KEYWORDS
    )


class DiagnosticRAG:
    """
    Recupera información del diagnóstico educativo almacenado
    en ChromaDB.
    """

    def __init__(
        self,
        chroma_path: Path = DIAGNOSTIC_CHROMA_PATH,
    ) -> None:
        self.chroma_path = Path(chroma_path)

        if not self.chroma_path.exists():
            raise FileNotFoundError(
                "La base vectorial del diagnóstico no existe.\n"
                "Ejecuta primero:\n"
                "python setup_diagnostic_rag.py"
            )

        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDINGS_MODEL
        )

        self.vectorstore = Chroma(
            persist_directory=str(self.chroma_path),
            embedding_function=self.embeddings,
            collection_name=DIAGNOSTIC_COLLECTION_NAME,
        )

    def count_documents(self) -> int:
        """Devuelve la cantidad de fragmentos guardados en Chroma."""

        data = self.vectorstore.get()

        return len(data.get("ids", []))

    def get_all_documents(self) -> list[Document]:
        """
        Recupera todos los fragmentos del diagnóstico.

        Se utiliza para producir resúmenes generales del documento.
        """

        data = self.vectorstore.get(
            include=["documents", "metadatas"]
        )

        contents = data.get("documents", [])
        metadatas = data.get("metadatas", [])

        documents: list[Document] = []

        for content, metadata in zip(
            contents,
            metadatas,
        ):
            if not content:
                continue

            documents.append(
                Document(
                    page_content=content,
                    metadata=metadata or {},
                )
            )

        documents.sort(
            key=lambda document: (
                document.metadata.get("page_number", 0),
                document.metadata.get("chunk_id", 0),
            )
        )

        return documents


    def build_search_query(
        self,
        question: str,
    ) -> tuple[str, str]:
        """
        Crea una consulta de recuperación según el tipo
        de pregunta realizada.
        """

        clean_question = question.strip()

        if is_diagnostic_question(clean_question):
            query_type = "diagnostico"

            search_query = (
                "principales dificultades de los estudiantes "
                "recordar instrucciones o comandos "
                "saber por dónde empezar "
                "entender la lógica "
                "corregir errores "
                "frustración al programar "
                "resultados porcentajes encuesta "
                f"{clean_question}"
            )

        else:
            query_type = "programacion"

            search_query = (
                "necesidades educativas de estudiantes "
                "explicaciones paso a paso "
                "lógica antes de sintaxis "
                "corrección explicativa de errores "
                "pistas progresivas "
                "adaptación al nivel "
                "frustración al programar "
                f"{clean_question}"
            )

        return search_query, query_type

    def retrieve(
        self,
        question: str,
    ) -> tuple[list[Document], str]:
        """
        Recupera documentos del diagnóstico y devuelve
        también el tipo de consulta detectado.
        """

        clean_question = question.strip()

        if not clean_question:
            return [], "programacion"

        if is_summary_question(clean_question):
            documents = self.get_all_documents()

            return documents, "diagnostico"

        search_query, query_type = self.build_search_query(
            clean_question
        )

        documents = self.vectorstore.similarity_search(
            query=search_query,
            k=RETRIEVAL_K,
        )

        return documents, query_type

    def format_context(
        self,
        documents: list[Document],
    ) -> str:
        """Convierte los documentos recuperados en texto."""

        if not documents:
            return (
                "No se recuperó información específica "
                "del diagnóstico."
            )

        context_parts: list[str] = []

        for document in documents:
            page_number = document.metadata.get(
                "page_number",
                "desconocida",
            )

            filename = document.metadata.get(
                "filename",
                "Documento diagnóstico",
            )

            content = document.page_content.strip()

            if not content:
                continue

            context_parts.append(
                f"Documento: {filename}\n"
                f"Página: {page_number}\n"
                f"Contenido:\n{content}"
            )

        if not context_parts:
            return (
                "Los documentos recuperados no contienen "
                "texto utilizable."
            )

        return "\n\n---\n\n".join(context_parts)

    def build_sources(
        self,
        documents: list[Document],
    ) -> list[dict]:
        """Construye una lista sin fuentes duplicadas."""

        sources: list[dict] = []
        seen_sources: set[tuple] = set()

        for document in documents:
            filename = document.metadata.get(
                "filename",
                "Documento diagnóstico",
            )

            page_number = document.metadata.get(
                "page_number",
                "desconocida",
            )

            source_key = (
                filename,
                page_number,
            )

            if source_key in seen_sources:
                continue

            seen_sources.add(source_key)

            sources.append(
                {
                    "filename": filename,
                    "page": page_number,
                }
            )

        return sources

    def get_context(
        self,
        question: str,
    ) -> tuple[str, str, list[dict]]:
        """
        Recupera el contexto, el tipo de consulta y las fuentes.
        """

        documents, query_type = self.retrieve(question)

        context = self.format_context(documents)
        sources = self.build_sources(documents)

        return context, query_type, sources


def main() -> None:
    """Prueba manual del sistema RAG."""

    rag = DiagnosticRAG()

    print("=" * 70)
    print(
        "Fragmentos almacenados en Chroma:",
        rag.count_documents(),
    )
    print("=" * 70)

    test_questions = [
        (
            "¿Cuál es la mayor dificultad que "
            "tienen mis compañeros de clase?"
        ),
        "¿Qué porcentaje siente frustración?",
        "Dame un resumen del documento.",
    ]

    for question in test_questions:
        print("\n" + "=" * 70)
        print("PREGUNTA:")
        print(question)

        context, query_type, sources = rag.get_context(
            question
        )

        print("\nTIPO DETECTADO:")
        print(query_type)

        print("\nFUENTES:")
        print(sources)

        print("\nCONTEXTO RECUPERADO:")
        print(context[:3000])


if __name__ == "__main__":
    main()
