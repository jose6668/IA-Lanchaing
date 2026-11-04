import streamlit as st

from Models.config import MEMORY_DB_PATH
from Services.chat_manager import ChatManager
from Services.user_manager import UserManager
from UI.asistente import (
    ask_assistant,
    clear_conversation,
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

        [data-testid="stTextInput"] input {
            background-color: #FFFFFF !important;
            color: var(--color-texto) !important;
            border: 1px solid var(--color-borde) !important;
            box-shadow: none !important;
        }

        [data-testid="stTextInput"] input::placeholder {
            color: rgba(23, 54, 66, 0.58) !important;
        }

        [data-testid="stTextInput"] button {
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

DEFAULT_ASSISTANT_TONE = "Normal, claro y amigable"
DEFAULT_LEARNING_MODE = "Aprendizaje guiado"


@st.cache_resource
def get_user_manager() -> UserManager:
    return UserManager(MEMORY_DB_PATH)


@st.cache_resource
def get_chat_manager() -> ChatManager:
    return ChatManager(MEMORY_DB_PATH)


user_manager = get_user_manager()
chat_manager = get_chat_manager()


def init_session_state() -> None:
    defaults = {
        "current_user": None,
        "current_chat_id": None,
        "messages": [],
        "session_id": None,
        "auth_mode": "Iniciar sesión",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def build_session_id() -> str | None:
    user = st.session_state.current_user
    chat_id = st.session_state.current_chat_id

    if not user or not chat_id:
        return None

    return chat_manager.build_session_id(user["username"], chat_id)


def load_current_chat_messages() -> None:
    session_id = build_session_id()

    if not session_id:
        st.session_state.messages = []
        st.session_state.session_id = None
        return

    st.session_state.session_id = session_id
    st.query_params["session_id"] = session_id
    st.session_state.messages = get_recent_conversation(session_id)


def set_current_chat(chat_id: str) -> None:
    st.session_state.current_chat_id = chat_id
    load_current_chat_messages()


def logout() -> None:
    st.session_state.current_user = None
    st.session_state.current_chat_id = None
    st.session_state.messages = []
    st.session_state.session_id = None
    st.query_params.clear()


def render_auth_screen() -> None:
    st.title("💻 Asistente para Aprender Programación")
    st.caption("Inicia sesión o crea un usuario para comenzar.")
    st.divider()

    st.session_state.auth_mode = st.radio(
        "Acceso",
        ["Iniciar sesión", "Crear usuario"],
        key="auth_mode_selector",
        horizontal=True,
        index=0 if st.session_state.auth_mode == "Iniciar sesión" else 1,
        label_visibility="collapsed",
    )

    if st.session_state.auth_mode == "Iniciar sesión":
        st.subheader("Iniciar sesión")

        with st.form("login_form"):
            username = st.text_input(
                "Nombre de usuario",
                placeholder="Ingresa tu usuario",
                key="login_username",
            )
            password = st.text_input(
                "Contraseña",
                type="password",
                key="login_password",
            )
            login_submitted = st.form_submit_button("Iniciar sesión")

            if login_submitted:
                success, user, message = user_manager.authenticate(
                    username=username,
                    password=password,
                )

                if success and user:
                    st.session_state.current_user = user
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
                    st.session_state.session_id = None
                    st.success(message)
                    st.rerun()

                st.error(message)

    if st.session_state.auth_mode == "Crear usuario":
        st.subheader("Crear usuario")

        with st.form("register_form"):
            name = st.text_input(
                "Nombre",
                key="register_name",
            )
            username = st.text_input(
                "Nombre de usuario",
                key="register_username",
            )
            password = st.text_input(
                "Contraseña",
                type="password",
                key="register_password",
            )
            confirm_password = st.text_input(
                "Confirmar contraseña",
                type="password",
                key="register_confirm_password",
            )
            register_submitted = st.form_submit_button("Crear usuario")

            if register_submitted:
                if password != confirm_password:
                    st.error("La confirmación de contraseña no coincide.")
                    return

                success, message = user_manager.create_user(
                    name=name,
                    username=username,
                    password=password,
                )

                if success:
                    auth_success, user, _ = user_manager.authenticate(
                        username=username,
                        password=password,
                    )
                    if auth_success and user:
                        st.session_state.current_user = user
                        st.session_state.current_chat_id = None
                        st.session_state.messages = []
                        st.session_state.session_id = None
                        st.success(message)
                        st.rerun()

                st.error(message)


def render_sidebar() -> None:
    user = st.session_state.current_user

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
        st.subheader("Chats")

        if st.button(
            "Nuevo chat",
            type="primary",
            use_container_width=True,
            key="new_chat_button",
        ):
            new_chat = chat_manager.create_chat(user["username"])
            set_current_chat(new_chat["chat_id"])
            st.rerun()

        chats = chat_manager.list_chats(user["username"])

        if chats:
            for chat in chats:
                is_active = chat["chat_id"] == st.session_state.current_chat_id
                label = chat["title"]

                if st.button(
                    label,
                    type="secondary" if is_active else "secondary",
                    use_container_width=True,
                    key=f"chat_{chat['chat_id']}",
                ):
                    set_current_chat(chat["chat_id"])
                    st.rerun()

                if is_active and st.button(
                    "Eliminar chat actual",
                    use_container_width=True,
                    key=f"delete_{chat['chat_id']}",
                ):
                    session_id = build_session_id()
                    if session_id:
                        clear_conversation(session_id)
                    chat_manager.delete_chat(user["username"], chat["chat_id"])
                    st.session_state.current_chat_id = None
                    st.session_state.messages = []
                    st.session_state.session_id = None
                    st.query_params.clear()
                    st.rerun()
        else:
            st.info("Crea un chat para comenzar.")

        st.divider()

        if st.session_state.current_chat_id and st.button(
            "🗑️ Limpiar chat",
            type="secondary",
            use_container_width=True,
            key="clear_chat_button",
        ):
            session_id = build_session_id()
            if session_id:
                clear_conversation(session_id)
            st.session_state.messages = []
            st.rerun()

        if st.button(
            "Cerrar sesión",
            use_container_width=True,
            key="logout_button",
        ):
            logout()
            st.rerun()


def render_user_header() -> None:
    user = st.session_state.current_user
    left, right = st.columns([3, 1])

    with left:
        st.title("💻 Asistente para Aprender Programación")
        st.caption("Tutor educativo guiado para aprender programación paso a paso")

    with right:
        st.markdown(
            f"""
            <div style="text-align: right; font-weight: 700; color: #1A77A3;">
                {user["name"]}<br>
                <span style="font-weight: 500;">@{user["username"]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


init_session_state()


if not st.session_state.current_user:
    render_auth_screen()
    st.stop()


render_sidebar()
render_user_header()
st.divider()

if not st.session_state.current_chat_id:
    st.info("Crea o selecciona un chat en la barra lateral para comenzar.")
    st.stop()


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
    if not st.session_state.session_id:
        load_current_chat_messages()

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
    chat_manager.touch_chat(
        st.session_state.current_user["username"],
        st.session_state.current_chat_id,
        first_message=user_input,
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

