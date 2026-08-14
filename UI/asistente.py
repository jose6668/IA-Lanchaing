import logging

import streamlit as st

from Graphs.learning_graph import create_learning_assistant_graph
from Models.config import MODEL_NAME, TEMPERATURE


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@st.cache_resource
def initialize_system():
    """
    Inicializa el grafo del asistente educativo.
    """

    assistant_graph = create_learning_assistant_graph()

    stored_documents = (
        assistant_graph
        .diagnostic_rag
        .count_documents()
    )

    logger.info(
        "LangGraph inicializado con %s fragmentos RAG.",
        stored_documents,
    )

    if stored_documents == 0:
        raise RuntimeError(
            "La coleccion de Chroma existe, pero no contiene "
            "fragmentos. Ejecuta nuevamente "
            "`python -m Services.setup_diagnostic_rag`."
        )

    return assistant_graph


def ask_assistant(
    question: str,
    tono: str,
    modo_aprendizaje: str,
) -> tuple[str, list[dict]]:
    """
    Procesa una pregunta utilizando LangGraph y el RAG diagnostico.
    """

    clean_question = question.strip()

    if not clean_question:
        return (
            "Escribe una pregunta o comparte un ejercicio "
            "para poder ayudarte.",
            [],
        )

    try:
        assistant_graph = initialize_system()

        result = assistant_graph.invoke(
            question=clean_question,
            tono=tono,
            modo_aprendizaje=modo_aprendizaje,
        )

        query_type = result.get("tipo_consulta", "programacion")
        diagnostic_sources = result.get("fuentes", [])
        response = result.get("respuesta")

        logger.info(
            "Tipo de consulta detectado: %s",
            query_type,
        )

        logger.info(
            "Fuentes recuperadas: %s",
            diagnostic_sources,
        )

        logger.info(
            "Historial de LangGraph: %s",
            result.get("historial", []),
        )

        if not response:
            return (
                "No se genero una respuesta final. Revisa el flujo "
                "de LangGraph y vuelve a intentarlo.",
                [],
            )

        return response, diagnostic_sources

    except FileNotFoundError as error:
        logger.exception(
            "No se encontro la base vectorial."
        )

        return str(error), []

    except RuntimeError as error:
        logger.exception(
            "La coleccion vectorial esta vacia."
        )

        return str(error), []

    except Exception as error:
        logger.exception(
            "Error al procesar la consulta."
        )

        return (
            "No pude procesar tu pregunta en este momento. "
            f"Detalle tecnico: {error}",
            [],
        )


def get_assistant_info() -> dict:
    """Devuelve informacion publica del asistente."""

    return {
        "tipo": "Tutor inteligente de programacion con LangGraph",
        "modelo": MODEL_NAME,
        "temperatura": TEMPERATURE,
        "contexto": "Diagnostico educativo con RAG",
        "orquestacion": "LangGraph",
    }
