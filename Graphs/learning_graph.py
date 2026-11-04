import logging
from operator import add
from typing import Annotated, Optional, TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from Models.classifier_prompt import CLASSIFIER_SYSTEM_PROMPT
from Models.config import MAX_HISTORY_MESSAGES, MEMORY_DB_PATH, MODEL_NAME, TEMPERATURE
from Prompts.prompt import PROGRAMMING_TEMPLATE
from Services.conversation_memory import SQLiteLimitedChatMessageHistory


logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "programacion",
    "revision_codigo",
    "historial",
    "restriccion",
}


class LearningAssistantState(TypedDict):
    question: str
    session_id: str
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
        self.memory_store: dict[str, SQLiteLimitedChatMessageHistory] = {}
        self.classifier_chain = self._build_classifier_chain()
        self.chain_with_memory = self._build_memory_chain()
        self.graph = self._build_graph()

    def _build_classifier_chain(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", CLASSIFIER_SYSTEM_PROMPT),
                ("human", "{question}"),
            ]
        )

        return prompt | self.llm | StrOutputParser()

    def _build_memory_chain(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", PROGRAMMING_TEMPLATE),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        chain = prompt_template | self.llm | StrOutputParser()

        return RunnableWithMessageHistory(
            chain,
            self.get_session_history,
            input_messages_key="question",
            history_messages_key="history",
        )

    def get_session_history(self, session_id: str) -> SQLiteLimitedChatMessageHistory:
        if session_id not in self.memory_store:
            self.memory_store[session_id] = SQLiteLimitedChatMessageHistory(
                session_id=session_id,
                db_path=MEMORY_DB_PATH,
                max_messages=MAX_HISTORY_MESSAGES,
            )

        return self.memory_store[session_id]

    def _build_graph(self):
        graph = StateGraph(LearningAssistantState)

        graph.add_node(
            "clasificar_consulta",
            self.clasificar_consulta_con_llm,
        )
        graph.add_node(
            "generar_respuesta_programacion",
            self.generar_respuesta_programacion,
        )
        graph.add_node("generar_revision_codigo", self.generar_revision_codigo)
        graph.add_node("responder_con_historial", self.responder_con_historial)
        graph.add_node("responder_restriccion", self.responder_restriccion)
        graph.add_node("respuesta_final", self.respuesta_final)

        graph.add_edge(START, "clasificar_consulta")
        graph.add_conditional_edges(
            "clasificar_consulta",
            self.enrutar_por_tipo_consulta,
            {
                "programacion": "generar_respuesta_programacion",
                "revision_codigo": "generar_revision_codigo",
                "historial": "responder_con_historial",
                "restriccion": "responder_restriccion",
            },
        )
        graph.add_edge("generar_respuesta_programacion", "respuesta_final")
        graph.add_edge("generar_revision_codigo", "respuesta_final")
        graph.add_edge("responder_con_historial", "respuesta_final")
        graph.add_edge("responder_restriccion", "respuesta_final")
        graph.add_edge("respuesta_final", END)

        return graph.compile()

    def clasificar_consulta_con_llm(
        self,
        state: LearningAssistantState,
    ) -> dict:
        raw_category = self.classifier_chain.invoke(
            {"question": state["question"]}
        )
        category = self._normalize_category(raw_category)

        return {
            "tipo_consulta": category,
            "historial": [f"Consulta clasificada como: {category}"],
        }

    def enrutar_por_tipo_consulta(
        self,
        state: LearningAssistantState,
    ) -> str:
        category = state.get("tipo_consulta", "restriccion")

        if category not in VALID_CATEGORIES:
            return "restriccion"

        return category

    def generar_respuesta_programacion(
        self,
        state: LearningAssistantState,
    ) -> dict:
        response = self._invoke_memory_chain(
            state,
            tipo_consulta="programacion",
        )

        return {
            "respuesta": response,
            "historial": ["Respuesta de programacion generada."],
        }

    def generar_revision_codigo(
        self,
        state: LearningAssistantState,
    ) -> dict:
        response = self._invoke_memory_chain(
            state,
            tipo_consulta="revision_codigo",
        )

        return {
            "respuesta": response,
            "historial": ["Revision de codigo procesada."],
        }

    def responder_con_historial(
        self,
        state: LearningAssistantState,
    ) -> dict:
        response = self._invoke_memory_chain(
            state,
            tipo_consulta="historial",
        )

        return {
            "respuesta": response,
            "historial": ["Respuesta generada desde memoria conversacional."],
        }

    def responder_restriccion(self, state: LearningAssistantState) -> dict:
        response = self._invoke_memory_chain(
            state,
            tipo_consulta="restriccion",
        )

        return {
            "respuesta": response,
            "historial": ["Consulta fuera de dominio restringida."],
        }

    def respuesta_final(self, state: LearningAssistantState) -> dict:
        return {"historial": ["Respuesta final preparada para Streamlit."]}

    def _invoke_memory_chain(
        self,
        state: LearningAssistantState,
        tipo_consulta: str,
    ) -> str:
        return self.chain_with_memory.invoke(
            {
                "question": state["question"],
                "tono": state["tono"],
                "modo_aprendizaje": state["modo_aprendizaje"],
                "tipo_consulta": tipo_consulta,
            },
            config={
                "configurable": {
                    "session_id": state["session_id"],
                }
            },
        )

    def invoke(
        self,
        question: str,
        tono: str,
        modo_aprendizaje: str,
        session_id: str,
    ) -> LearningAssistantState:
        initial_state: LearningAssistantState = {
            "question": question.strip(),
            "session_id": session_id,
            "tono": tono,
            "modo_aprendizaje": modo_aprendizaje,
            "tipo_consulta": "",
            "respuesta": None,
            "historial": [],
        }

        return self.graph.invoke(initial_state)

    def _normalize_category(self, raw_category: str) -> str:
        normalized = (
            raw_category
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        for category in VALID_CATEGORIES:
            if category in normalized:
                return category

        logger.warning(
            "Categoria de clasificacion no valida: %s",
            raw_category,
        )

        return "restriccion"


def create_learning_assistant_graph() -> LearningAssistantGraph:
    return LearningAssistantGraph()
