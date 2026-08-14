import streamlit as st
from uuid import uuid4

from UI.asistente import (
    ask_assistant,
    clear_conversation,
    get_last_conversation_session_id,
    get_recent_conversation,
)

st.set_page_config(
    page_title="Asistente de Programación",
    page_icon="💻",
    layout="wide",
)

st.markdown(
    """
    <style>
        :root {
            --color-celeste: #95D1DC;
            --color-menta: #E7F0EA;
            --color-azul: #1A77A3;
            --color-azul-oscuro: #155F82;
            --color-superficie: #F7FBFA;
            --color-texto: #173642;
            --color-borde: rgba(149, 209, 220, 0.75);
        }

        .stApp {
            background:
                linear-gradient(180deg, #E7F0EA 0%, #F7FBFA 34%, #FFFFFF 100%);
            color: var(--color-texto);
        }

        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stBottom"] {
            background: var(--color-superficie) !important;
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stBottom"] > div,
        [data-testid="stBottom"] > div > div,
        [data-testid="stBottom"] section,
        [data-testid="stBottom"] form,
        .stChatFloatingInputContainer,
        div:has(> [data-testid="stChatInput"]),
        div:has([data-testid="stChatInput"]) {
            background: var(--color-superficie) !important;
        }

        h1, h2, h3 {
            color: var(--color-azul);
        }

        p, li, label, span, div {
            color: var(--color-texto);
        }

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {
            color: var(--color-texto) !important;
            line-height: 1.7;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #E7F0EA 0%, #F8FCFB 100%);
            border-right: 4px solid var(--color-celeste);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stMarkdown strong {
            color: var(--color-azul);
        }

        .sidebar-guide {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--color-borde);
            border-left: 5px solid var(--color-azul);
            border-radius: 8px;
            padding: 1rem;
            color: var(--color-texto);
            line-height: 1.65;
        }

        .sidebar-guide strong {
            color: var(--color-azul);
        }

        .stButton > button {
            background-color: var(--color-azul);
            border: 1px solid var(--color-azul);
            color: #FFFFFF;
            font-weight: 600;
        }

        .stButton > button:hover {
            background-color: var(--color-azul-oscuro);
            border-color: var(--color-azul-oscuro);
            color: #FFFFFF;
        }

        [data-testid="stAlert"] {
            background-color: rgba(149, 209, 220, 0.28);
            border-radius: 8px;
            border-left: 5px solid var(--color-celeste);
        }

        [data-testid="stAlert"] *,
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] li {
            color: var(--color-texto) !important;
        }

        [data-testid="stChatMessage"] {
            background-color: rgba(255, 255, 255, 0.78);
            border-left: 5px solid var(--color-celeste);
            border-radius: 8px;
            padding: 0.65rem;
            box-shadow: 0 8px 22px rgba(26, 119, 163, 0.07);
        }

        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] code {
            color: var(--color-texto) !important;
        }

        [data-testid="stChatMessage"]:has(
            [data-testid="chatAvatarIcon-user"]
        ) {
            border-left-color: var(--color-azul);
        }

        [data-testid="stChatInput"] {
            background: var(--color-superficie) !important;
            border-top: 0;
            padding-bottom: 0.75rem;
        }

        [data-testid="stChatInput"] > div {
            background-color: #FFFFFF !important;
            border: 2px solid var(--color-celeste) !important;
            box-shadow: none !important;
        }

        [data-testid="stChatInput"] textarea {
            background-color: #FFFFFF !important;
            color: var(--color-texto) !important;
        }

        [data-testid="stChatInput"] button {
            color: var(--color-azul) !important;
        }

        hr {
            border-color: rgba(26, 119, 163, 0.22);
        }

        .palette-footer {
            color: var(--color-azul);
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "session_id" not in st.session_state:
    query_session_id = st.query_params.get("session_id")
    if query_session_id:
        st.session_state.session_id = query_session_id
    else:
        last_session_id = get_last_conversation_session_id()
        st.session_state.session_id = (
            last_session_id
            if last_session_id
            else f"streamlit-{uuid4().hex}"
        )
    st.query_params["session_id"] = st.session_state.session_id

if "messages" not in st.session_state:
    st.session_state.messages = get_recent_conversation(
        st.session_state.session_id
    )

DEFAULT_ASSISTANT_TONE = "Normal, claro y amigable"
DEFAULT_LEARNING_MODE = "Aprendizaje guiado"


st.title(
    "💻 Asistente para Aprender Programación"
)

st.caption(
    "Tutor educativo guiado para aprender programación paso a paso"
)

st.divider()



with st.sidebar:
    st.header("Guía de uso")

    st.markdown(
        """
        <div class="sidebar-guide">
            <strong>Este asistente te ayuda a aprender programación.</strong>
            Escribe una pregunta, comparte una duda o pega un fragmento de
            código. Recibirás orientación paso a paso, con pistas y preguntas
            para que puedas construir la solución por tu cuenta.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        "🗑️ Limpiar chat",
        type="secondary",
        use_container_width=True,
        key="clear_chat_button",
    ):
        clear_conversation(st.session_state.session_id)
        st.session_state.messages = []
        st.session_state.session_id = f"streamlit-{uuid4().hex}"
        st.query_params["session_id"] = st.session_state.session_id
        st.rerun()


chat_column, topics_column = st.columns(
    [2, 1]
)

with chat_column:
    st.markdown(
        "### 💬 Chat de aprendizaje"
    )

    if not st.session_state.messages:
        st.info(
            "Escribe una pregunta de programación "
            "o comparte un fragmento de código para recibir ayuda guiada."
        )

    for message in st.session_state.messages:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )


with topics_column:
    st.markdown(
        "### 📚 Temas sugeridos"
    )

    st.info(
        """
        Puedes preguntar:

        - ¿Qué es una variable?
        - ¿Qué es un ciclo `for`?
        - ¿Cómo funciona un `if`?
        - Explícame las listas en Python.
        - Ayúdame a corregir este código.
        - ¿Cómo divido este problema en pasos?
        - ¿Qué debo revisar antes de ejecutar mi programa?
        """
    )



user_input = st.chat_input(
    "Escribe tu pregunta sobre programación...",
    key="main_chat_input",
)

if user_input:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.spinner(
        "💻 Analizando tu pregunta..."
    ):
        response, _ = (
            ask_assistant(
                question=user_input,
                tono=DEFAULT_ASSISTANT_TONE,
                modo_aprendizaje=DEFAULT_LEARNING_MODE,
                session_id=st.session_state.session_id,
            )
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )

    st.rerun()



st.divider()

st.markdown(
    """
    <div class="palette-footer" style="text-align: center;">
        💻 Asistente educativo de programación
    </div>
    """,
    unsafe_allow_html=True,
)

