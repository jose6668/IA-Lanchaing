import streamlit as st
from html import escape
from UI.theme import ICON_PATH, apply_theme, brand, icon_uri

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
    page_icon=str(ICON_PATH),
    layout="wide",
)

apply_theme()

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
    st.markdown('<div class="auth-heading">' + brand() + '<h1>Tu próxima idea empieza aquí</h1><p>Aprende programación a tu ritmo, con un tutor que te acompaña.</p></div>', unsafe_allow_html=True)
    with st.container(key="auth_card"):
        st.session_state.auth_mode = st.radio(
            "Acceso", ["Iniciar sesión", "Crear usuario"],
            key="auth_mode_selector", horizontal=True, label_visibility="collapsed",
        )
        render_auth_form()
        st.caption("Aprende · Practica · Construye")


def render_auth_form() -> None:
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
                placeholder="Ingresa tu contraseña",
                key="login_password",
            )
            login_submitted = st.form_submit_button("Acceder →", type="primary", use_container_width=True)

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
            register_submitted = st.form_submit_button("Crear usuario →", type="primary", use_container_width=True)

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
        st.markdown(brand(), unsafe_allow_html=True)
        st.write("")
        if st.button(
            "＋ Nuevo chat",
            type="primary",
            use_container_width=True,
            key="new_chat_button",
        ):
            new_chat = chat_manager.create_chat(user["username"])
            set_current_chat(new_chat["chat_id"])
            st.rerun()

        st.markdown('<div class="eyebrow">CONVERSACIONES</div>', unsafe_allow_html=True)
        chats = chat_manager.list_chats(user["username"])

        if chats:
            for chat in chats:
                is_active = chat["chat_id"] == st.session_state.current_chat_id
                label = chat["title"]

                if st.button(
                    label,
                    type="primary" if is_active else "secondary",
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

        st.markdown('<div class="sidebar-guide"><strong>💡 Guía de uso</strong><p>Pregunta, comparte código o pide ejemplos. Te acompañamos con pistas y explicaciones paso a paso.</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="profile"><span class="avatar">{escape(user["name"][:1].upper())}</span><div><strong>{escape(user["name"])}</strong><small>Estudiante</small></div></div>', unsafe_allow_html=True)
        if st.button(
            "Cerrar sesión",
            use_container_width=True,
            key="logout_button",
        ):
            logout()
            st.rerun()


def render_user_header() -> None:
    user = st.session_state.current_user
    st.markdown(f"""
        <div class="topline"><span>Tu espacio de aprendizaje</span><span class="user-pill">{escape(user['name'])} · Estudiante</span></div>
        <section class="welcome">
            <div><div class="eyebrow">APRENDE A CREAR</div><h1>¡Hola, {escape(user['name'])}!</h1>
            <h2>¿Qué quieres aprender hoy?</h2><p>Tu asistente de programación, listo para ayudarte paso a paso.</p></div>
            <img src="{icon_uri()}" alt="Robot tutor de programación" />
        </section>
    """, unsafe_allow_html=True)


def render_topics() -> None:
    topics = [
        ("🐍", "Python", "Aprende desde cero con ejemplos prácticos.", "Quiero aprender Python desde cero. ¿Por dónde empiezo?"),
        ("🎮", "Videojuegos", "Da vida a tus ideas con código.", "¿Cómo puedo programar mi primer videojuego?"),
        ("🤖", "Robótica", "Conecta programación y creatividad.", "Explícame cómo empezar a programar un proyecto con Arduino."),
        ("💡", "Dudas rápidas", "Resuelve una duda, paso a paso.", "¿Cómo puedo dividir un problema de programación en pasos?"),
    ]
    for column, (symbol, title, description, prompt) in zip(st.columns(4), topics):
        with column, st.container(key="topic_" + title):
            st.markdown(f'<div class="topic-icon">{symbol}</div><h3>{title}</h3><p>{description}</p>', unsafe_allow_html=True)
            if st.button(f"Explorar {title} →", key="choose_" + title, use_container_width=True):
                st.session_state.pending_prompt = prompt




init_session_state()


if not st.session_state.current_user:
    render_auth_screen()
    st.stop()


render_sidebar()
render_user_header()
render_topics()

if not st.session_state.messages:
    st.markdown("""<section class="empty-chat"><div class="bubble-art">〈 / 〉</div>
        <h3>Comienza una conversación</h3><p>Escribe tu pregunta abajo o elige un tema para empezar.<br>
        Vamos a aprender programación de forma clara y sencilla.</p></section>""", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=str(ICON_PATH) if message["role"] == "assistant" else None):
        st.markdown(message["content"])

st.markdown('<div class="palette-footer">Asistente de Programación · Aprende hoy, construye el mañana.</div>', unsafe_allow_html=True)
user_input = st.chat_input("Escribe tu pregunta aquí…", key="main_chat_input")
user_input = user_input or st.session_state.pop("pending_prompt", None)

if user_input:
    if not st.session_state.current_chat_id:
        new_chat = chat_manager.create_chat(st.session_state.current_user["username"])
        set_current_chat(new_chat["chat_id"])
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

