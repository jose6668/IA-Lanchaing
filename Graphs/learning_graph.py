import logging
from operator import add
from typing import Annotated, Optional, TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from Models.config import *
from Prompts.prompt import *
from Services.diagnostic_rag import *


logger = logging.getLogger(__name__)


class LearningAssistantState(TypedDict):
    question: str
    tono: str
    modo_aprendizaje: str
    tipo_consulta: str
    contexto_diagnostico: Optional[str]
    fuentes: list[dict]
    respuesta: Optional[str]
    requiere_revision_codigo: bool
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
        self.chain = (
            self.prompt_template
            | self.llm
            | StrOutputParser()
        )
        self.diagnostic_rag = DiagnosticRAG()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(LearningAssistantState)

        graph.add_node("clasificar_consulta", self.clasificar_consulta)
        graph.add_node("recuperar_diagnostico", self.recuperar_diagnostico)
        graph.add_node(
            "generar_respuesta_programacion",
            self.generar_respuesta_programacion,
        )
        graph.add_node(
            "generar_respuesta_diagnostico",
            self.generar_respuesta_diagnostico,
        )
        graph.add_node("analizar_codigo", self.analizar_codigo)
        graph.add_node("respuesta_final", self.respuesta_final)

        graph.add_edge(START, "clasificar_consulta")
        graph.add_conditional_edges(
            "clasificar_consulta",
            self.enrutar_por_tipo_consulta,
            {
                "diagnostico": "recuperar_diagnostico",
                "programacion": "generar_respuesta_programacion",
                "revision_codigo": "analizar_codigo",
            },
        )
        graph.add_edge(
            "recuperar_diagnostico",
            "generar_respuesta_diagnostico",
        )
        graph.add_edge("generar_respuesta_diagnostico", "respuesta_final")
        graph.add_edge("generar_respuesta_programacion", "respuesta_final")
        graph.add_edge("analizar_codigo", "respuesta_final")
        graph.add_edge("respuesta_final", END)

        return graph.compile()

    def clasificar_consulta(self, state: LearningAssistantState) -> dict:
        question = state["question"].strip()
        normalized_question = normalize_text(question)
        normalized_mode = normalize_text(state.get("modo_aprendizaje", ""))

        code_indicators = {
            "codigo",
            "error",
            "bug",
            "traceback",
            "exception",
            "revisar",
            "corrige",
            "corregir",
        }

        if is_summary_question(question) or is_diagnostic_question(question):
            tipo_consulta = "diagnostico"
            requiere_revision_codigo = False
        elif "revision" in normalized_mode or any(
            indicator in normalized_question
            for indicator in code_indicators
        ):
            tipo_consulta = "revision_codigo"
            requiere_revision_codigo = True
        else:
            tipo_consulta = "programacion"
            requiere_revision_codigo = False

        return {
            "tipo_consulta": tipo_consulta,
            "requiere_revision_codigo": requiere_revision_codigo,
            "historial": [f"Consulta clasificada como: {tipo_consulta}"],
        }

    def enrutar_por_tipo_consulta(
        self,
        state: LearningAssistantState,
    ) -> str:
        return state.get("tipo_consulta", "programacion")

    def recuperar_diagnostico(self, state: LearningAssistantState) -> dict:
        context, query_type, sources = self.diagnostic_rag.get_context(
            state["question"]
        )

        logger.info(
            "LangGraph recupero %s fuentes para consulta %s.",
            len(sources),
            query_type,
        )

        return {
            "tipo_consulta": query_type,
            "contexto_diagnostico": context,
            "fuentes": sources,
            "historial": [
                f"Contexto diagnostico recuperado: {len(sources)} fuentes"
            ],
        }

    def generar_respuesta_programacion(
        self,
        state: LearningAssistantState,
    ) -> dict:
        response = self._invoke_chain(
            state,
            tipo_consulta="programacion",
            contexto_diagnostico=(
                "No se debe usar contexto diagnostico para esta consulta."
            ),
        )

        return {
            "respuesta": response,
            "fuentes": [],
            "historial": [
                "Respuesta de programacion generada sin RAG diagnostico."
            ],
        }

    def generar_respuesta_diagnostico(
        self,
        state: LearningAssistantState,
    ) -> dict:
        sources = state.get("fuentes", [])

        if not sources:
            return {
                "respuesta": (
                    "La pregunta fue identificada como una consulta "
                    "sobre el diagnostico, pero no se recuperaron "
                    "fragmentos del documento. Revisa la base vectorial "
                    "y reconstruye el diagnostico."
                ),
                "historial": ["No se encontraron fuentes diagnosticas."],
            }

        response = self._invoke_chain(
            state,
            tipo_consulta="diagnostico",
            contexto_diagnostico=(
                state.get("contexto_diagnostico")
                or "No se recupero informacion especifica."
            ),
        )

        return {
            "respuesta": response,
            "historial": [
                "Respuesta diagnostica generada con contexto RAG."
            ],
        }

    def analizar_codigo(self, state: LearningAssistantState) -> dict:
        response = self._invoke_chain(
            state,
            tipo_consulta="programacion",
            contexto_diagnostico=(
                "No se debe usar contexto diagnostico para revision de codigo."
            ),
        )

        return {
            "respuesta": response,
            "fuentes": [],
            "historial": [
                "Revision de codigo procesada como consulta de programacion."
            ],
        }

    def respuesta_final(self, state: LearningAssistantState) -> dict:
        return {
            "historial": ["Respuesta final preparada para Streamlit."]
        }

    def _invoke_chain(
        self,
        state: LearningAssistantState,
        tipo_consulta: str,
        contexto_diagnostico: str,
    ) -> str:
        return self.chain.invoke(
            {
                "question": state["question"],
                "tono": state["tono"],
                "modo_aprendizaje": state["modo_aprendizaje"],
                "tipo_consulta": tipo_consulta,
                "contexto_diagnostico": contexto_diagnostico,
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
            "contexto_diagnostico": None,
            "fuentes": [],
            "respuesta": None,
            "requiere_revision_codigo": False,
            "historial": [],
        }

        return self.graph.invoke(initial_state)


def create_learning_assistant_graph() -> LearningAssistantGraph:
    return LearningAssistantGraph()
