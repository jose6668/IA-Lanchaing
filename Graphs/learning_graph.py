import logging
from operator import add
from typing import Annotated, Optional, TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from Models.config import MODEL_NAME, TEMPERATURE
from Prompts.prompt import PROGRAMMING_TEMPLATE


logger = logging.getLogger(__name__)


class LearningAssistantState(TypedDict):
    question: str
    tono: str
    modo_aprendizaje: str
    tipo_consulta: str
    respuesta: Optional[str]
    historial: Annotated[list[str], add]


class LearningAssistantGraph:
    """Orquesta el flujo del asistente educativo con LangGraph."""

    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_retries=2,
        )
        self.prompt_template = PromptTemplate.from_template(
            PROGRAMMING_TEMPLATE
        )
        self.chain = self.prompt_template | self.llm | StrOutputParser()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(LearningAssistantState)

        graph.add_node("clasificar_consulta", self.clasificar_consulta)
        graph.add_node(
            "generar_respuesta_programacion",
            self.generar_respuesta_programacion,
        )
        graph.add_node("analizar_codigo", self.analizar_codigo)
        graph.add_node("responder_restriccion", self.responder_restriccion)
        graph.add_node("respuesta_final", self.respuesta_final)

        graph.add_edge(START, "clasificar_consulta")
        graph.add_conditional_edges(
            "clasificar_consulta",
            self.enrutar_por_tipo_consulta,
            {
                "programacion": "generar_respuesta_programacion",
                "revision_codigo": "analizar_codigo",
                "restriccion": "responder_restriccion",
            },
        )
        graph.add_edge("generar_respuesta_programacion", "respuesta_final")
        graph.add_edge("analizar_codigo", "respuesta_final")
        graph.add_edge("responder_restriccion", "respuesta_final")
        graph.add_edge("respuesta_final", END)

        return graph.compile()

    def clasificar_consulta(self, state: LearningAssistantState) -> dict:
        question = state["question"].strip()
        normalized_question = self._normalize_text(question)

        code_indicators = {
            "codigo",
            "error",
            "bug",
            "traceback",
            "exception",
            "revisar",
            "corrige",
            "corregir",
            "syntaxerror",
            "typeerror",
            "valueerror",
            "print(",
            "def ",
            "class ",
        }

        programming_indicators = {
            "programacion",
            "python",
            "variable",
            "funcion",
            "lista",
            "tupla",
            "diccionario",
            "ciclo",
            "bucle",
            "for",
            "while",
            "if",
            "else",
            "clase",
            "objeto",
            "metodo",
            "algoritmo",
        }

        if any(indicator in normalized_question for indicator in code_indicators):
            tipo_consulta = "revision_codigo"
        elif any(
            indicator in normalized_question
            for indicator in programming_indicators
        ):
            tipo_consulta = "programacion"
        else:
            tipo_consulta = "restriccion"

        return {
            "tipo_consulta": tipo_consulta,
            "historial": [f"Consulta clasificada como: {tipo_consulta}"],
        }

    def enrutar_por_tipo_consulta(
        self,
        state: LearningAssistantState,
    ) -> str:
        return state.get("tipo_consulta", "restriccion")

    def generar_respuesta_programacion(
        self,
        state: LearningAssistantState,
    ) -> dict:
        response = self._invoke_chain(
            state,
            tipo_consulta="programacion",
        )

        return {
            "respuesta": response,
            "historial": ["Respuesta de programacion generada."],
        }

    def analizar_codigo(self, state: LearningAssistantState) -> dict:
        response = self._invoke_chain(
            state,
            tipo_consulta="revision_codigo",
        )

        return {
            "respuesta": response,
            "historial": ["Revision de codigo procesada."],
        }

    def responder_restriccion(self, state: LearningAssistantState) -> dict:
        response = self._invoke_chain(
            state,
            tipo_consulta="restriccion",
        )

        return {
            "respuesta": response,
            "historial": ["Consulta fuera de dominio restringida."],
        }

    def respuesta_final(self, state: LearningAssistantState) -> dict:
        return {"historial": ["Respuesta final preparada para Streamlit."]}

    def _invoke_chain(
        self,
        state: LearningAssistantState,
        tipo_consulta: str,
    ) -> str:
        return self.chain.invoke(
            {
                "question": state["question"],
                "tono": state["tono"],
                "modo_aprendizaje": state["modo_aprendizaje"],
                "tipo_consulta": tipo_consulta,
            }
        )

    def invoke(
        self,
        question: str,
        tono: str,
        modo_aprendizaje: str,
    ) -> LearningAssistantState:
        initial_state: LearningAssistantState = {
            "question": question.strip(),
            "tono": tono,
            "modo_aprendizaje": modo_aprendizaje,
            "tipo_consulta": "",
            "respuesta": None,
            "historial": [],
        }

        return self.graph.invoke(initial_state)

    def _normalize_text(self, text: str) -> str:
        translation = str.maketrans(
            "áéíóúüñÁÉÍÓÚÜÑ",
            "aeiouunAEIOUUN",
        )

        return text.lower().strip().translate(translation)


def create_learning_assistant_graph() -> LearningAssistantGraph:
    return LearningAssistantGraph()
