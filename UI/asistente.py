import logging

import streamlit as st

from Graphs.learning_graph import create_learning_assistant_graph
from Models.config import MODEL_NAME, TEMPERATURE


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@st.cache_resource
def initialize_system():
    """Inicializa el grafo del asistente educativo."""

    assistant_graph = create_learning_assistant_graph()

    logger.info("LangGraph inicializado correctamente.")

    return assistant_graph


def ask_assistant(
    question: str,
    tono: str,
    modo_aprendizaje: str,
    session_id: str,
) -> tuple[str, list[dict]]:
    """Procesa una pregunta utilizando LangGraph."""

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
            session_id=session_id,
        )

        query_type = result.get("tipo_consulta", "restriccion")
        response = result.get("respuesta")

        logger.info("Tipo de consulta detectado: %s", query_type)
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

        return response, []

    except Exception as error:
        logger.exception("Error al procesar la consulta.")

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
        "contexto": "Programacion, revision de codigo y memoria conversacional",
        "orquestacion": "LangGraph",
    }
