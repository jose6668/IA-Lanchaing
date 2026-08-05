import streamlit as st

from UI.asistente import ask_assistant, get_assistant_info


st.set_page_config(
    page_title="Asistente de Programacion",
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
        }

        .stApp {
            background: var(--color-superficie);
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
            border-radius: 8px;
            border-left: 5px solid var(--color-celeste);
        }

        [data-testid="stChatMessage"] {
            background-color: rgba(231, 240, 234, 0.52);
            border-left: 5px solid var(--color-celeste);
            border-radius: 8px;
            padding: 0.5rem;
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
            background-color: var(--color-superficie) !important;
            border: 2px solid var(--color-celeste) !important;
            box-shadow: none !important;
        }

        [data-testid="stChatInput"] textarea {
            background-color: var(--color-superficie) !important;
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

if "messages" not in st.session_state:
    st.session_state.messages = []

DEFAULT_ASSISTANT_TONE = "Normal, claro y amigable"
DEFAULT_LEARNING_MODE = "Aprendizaje guiado"

st.title("💻 Asistente para Aprender Programacion")

st.caption(
    "Tutor educativo personalizado para programacion y revision de codigo"
)

st.divider()

with st.sidebar:
    st.header("📋 Informacion del sistema")

    assistant_info = get_assistant_info()

    st.markdown("**🤖 Tipo de asistente:**")
    st.info(assistant_info["tipo"])
    st.divider()

    st.markdown("**🎓 Modo de aprendizaje:**")
    st.info(
        "Aprendizaje guiado: el asistente orienta paso a paso "
        "con preguntas y pistas, sin entregar la solucion completa "
        "de inmediato."
    )

    st.divider()

    if st.button(
        "🗑️ Limpiar chat",
        type="secondary",
        use_container_width=True,
        key="clear_chat_button",
    ):
        st.session_state.messages = []
        st.cache_resource.clear()
        st.rerun()

chat_column, topics_column = st.columns([2, 1])

with chat_column:
    st.markdown("### 💬 Chat de aprendizaje")

    if not st.session_state.messages:
        st.info(
            "Escribe una pregunta de programacion o comparte codigo "
            "para revisarlo paso a paso."
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

with topics_column:
    st.markdown("### 📚 Temas sugeridos")

    st.info(
        """
        Puedes preguntar:

        - ¿Que es una variable?
        - ¿Que es un ciclo `for`?
        - ¿Como funciona un `if`?
        - Explicame las listas en Python.
        - Ayudame a corregir este codigo.
        - ¿Por que me sale este error?
        """
    )

user_input = st.chat_input(
    "Escribe tu pregunta sobre programacion...",
    key="main_chat_input",
)

if user_input:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.spinner("💻 Analizando tu pregunta..."):
        response, _sources = ask_assistant(
            question=user_input,
            tono=DEFAULT_ASSISTANT_TONE,
            modo_aprendizaje=DEFAULT_LEARNING_MODE,
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
        💻 Asistente educativo de programacion
    </div>
    """,
    unsafe_allow_html=True,
)
