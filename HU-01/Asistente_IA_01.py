from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

from config import *
from prompt import *


@st.cache_resource
def initialize_system():
    
    llm = ChatOpenAI(
        model_name=MODEL_NAME,
        temperature=TEMPERATURE
    )
    
    prompt = PromptTemplate.from_template(PROGRAMMING_TEMPLATE)

    chain = (
        prompt
        | llm
        | StrOutputParser()
    )

    return chain


def ask_assistent(question, tono):
    try:
        chain = initialize_system()

        response = chain.invoke({
            "question": question,
            "tono": tono
        })

        return response

    except Exception as e:
        error_msg = f"Error al procesar la solicitud: {str(e)}"
        return error_msg
    

def get_assitent_info():
    return {
        "tipo": "Asistente educativo de Programación",
        "modelo": MODEL_NAME,
        "temperatura": TEMPERATURE
    }

       