import logging

import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from Models.config import MODEL_NAME, TEMPERATURE
from Services.diagnostic_rag import DiagnosticRAG
from Prompts.prompt import PROGRAMMING_TEMPLATE


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@st.cache_resource
def initialize_system():
    """
    Inicializa el modelo, el prompt y el sistema RAG.
    """

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_retries=2,
    )

    prompt_template = PromptTemplate.from_template(
        PROGRAMMING_TEMPLATE
    )

    chain = (
        prompt_template
        | llm
        | StrOutputParser()
    )

    diagnostic_rag = DiagnosticRAG()

    stored_documents = diagnostic_rag.count_documents()

    logger.info(
        "Sistema RAG inicializado con %s fragmentos.",
        stored_documents,
    )

    if stored_documents == 0:
        raise RuntimeError(
            "La colección de Chroma existe, pero no contiene "
            "fragmentos. Ejecuta nuevamente "
            "`python setup_diagnostic_rag.py`."
        )

    return chain, diagnostic_rag


def ask_assistant(
    question: str,
    tono: str,
    modo_aprendizaje: str,
) -> tuple[str, list[dict]]:
    """
    Procesa una pregunta utilizando el diagnóstico educativo.
    """

    clean_question = question.strip()

    if not clean_question:
        return (
            "Escribe una pregunta o comparte un ejercicio "
            "para poder ayudarte.",
            [],
        )

    try:
        chain, diagnostic_rag = initialize_system()

        (
            diagnostic_context,
            query_type,
            diagnostic_sources,
        ) = diagnostic_rag.get_context(
            clean_question
        )

        logger.info(
            "Tipo de consulta detectado: %s",
            query_type,
        )

        logger.info(
            "Fuentes recuperadas: %s",
            diagnostic_sources,
        )

        logger.info(
            "Longitud del contexto recuperado: %s caracteres",
            len(diagnostic_context),
        )

        if (
            query_type == "diagnostico"
            and not diagnostic_sources
        ):
            return (
                "La pregunta fue identificada como una consulta "
                "sobre el diagnóstico, pero no se recuperaron "
                "fragmentos del documento. Revisa la terminal "
                "y ejecuta `python diagnostic_rag.py`.",
                [],
            )

        response = chain.invoke(
            {
                "question": clean_question,
                "tono": tono,
                "modo_aprendizaje": modo_aprendizaje,
                "tipo_consulta": query_type,
                "contexto_diagnostico": diagnostic_context,
            }
        )

        return response, diagnostic_sources

    except FileNotFoundError as error:
        logger.exception(
            "No se encontró la base vectorial."
        )

        return str(error), []

    except RuntimeError as error:
        logger.exception(
            "La colección vectorial está vacía."
        )

        return str(error), []

    except Exception as error:
        logger.exception(
            "Error al procesar la consulta."
        )

        return (
            "No pude procesar tu pregunta en este momento. "
            f"Detalle técnico: {error}",
            [],
        )


def get_assistant_info() -> dict:
    """Devuelve información pública del asistente."""

    return {
        "tipo": "Tutor inteligente de programación",
        "modelo": MODEL_NAME,
        "temperatura": TEMPERATURE,
        "contexto": "Diagnóstico educativo con RAG",
    }