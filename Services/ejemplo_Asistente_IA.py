from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

from Models.config import *
from Prompts.prompt import *


@st.cache_resource
def initialize_system():
    """
    Inicializa el modelo, el prompt y la cadena LCEL.

    La función se almacena en caché para evitar crear una nueva
    instancia del modelo en cada recarga de Streamlit.
    """

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE
    )

    prompt_template = PromptTemplate.from_template(
        PROGRAMMING_TEMPLATE
    )

    chain = (
        prompt_template
        | llm
        | StrOutputParser()
    )

    return chain


def ask_assistent(
    question: str,
    tono: str,
    modo_aprendizaje: str
) -> str:
    """
    Envía la pregunta, el tono y el modo de aprendizaje al asistente.
    """

    if not question.strip():
        return "Por favor, escribe una pregunta o comparte un ejercicio."

    try:
        chain = initialize_system()

        response = chain.invoke({
            "question": question,
            "tono": tono,
            "modo_aprendizaje": modo_aprendizaje
        })

        return response

    except Exception as error:
        return (
            "Ocurrió un error al procesar la solicitud. "
            f"Detalle: {str(error)}"
        )


def get_assitent_info():
    return {
        "tipo": "Asistente educativo de programación",
        "modelo": MODEL_NAME,
        "temperatura": TEMPERATURE
    }