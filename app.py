import streamlit as st

from UI.asistente import *
from Models.config import *
from Services.setup_diagnostic_rag import DiagnosticDocumentProcessor

st.set_page_config(
    page_title="Asistente de Programación",
    page_icon="💻",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "tono_asistente" not in st.session_state:
    st.session_state.tono_asistente = (
        "Útil y amigable"
    )

if "modo_aprendizaje" not in st.session_state:
    st.session_state.modo_aprendizaje = (
        "Aprendizaje guiado"
    )


def diagnostic_is_configured() -> bool:
    """Comprueba que exista el índice vectorial."""

    return DIAGNOSTIC_CHROMA_PATH.exists()


def configure_diagnostic() -> bool:
    """Procesa el PDF y reconstruye ChromaDB."""

    try:
        processor = (
            DiagnosticDocumentProcessor()
        )

        vectorstore = processor.setup()

        return vectorstore is not None

    except Exception as error:
        st.error(
            "No fue posible configurar "
            f"el diagnóstico: {error}"
        )

        return False



st.title(
    "💻 Asistente para Aprender Programación"
)

st.caption(
    "Tutor educativo personalizado mediante "
    "un diagnóstico de necesidades estudiantiles"
)

st.divider()



with st.sidebar:
    st.header("📋 Información del sistema")

    assistant_info = get_assistant_info()

    st.markdown("**🤖 Tipo de asistente:**")
    st.info(assistant_info["tipo"])
    st.divider()


    st.subheader("📄 Diagnóstico educativo")

    if DIAGNOSTIC_PDF_PATH.exists():
        st.success("PDF encontrado")
    else:
        st.error(
            "No se encontró el PDF dentro "
            "de la carpeta docs."
        )

    if diagnostic_is_configured():
        st.success("Base vectorial configurada")
    else:
        st.warning(
            "La base vectorial todavía "
            "no está configurada."
        )

    if st.button(
        "🔄 Procesar o reconstruir diagnóstico",
        use_container_width=True,
        key="configure_diagnostic_button",
    ):
        with st.spinner(
            "Procesando el documento..."
        ):
            if configure_diagnostic():
                st.success(
                    "Diagnóstico procesado correctamente."
                )

                # Elimina los recursos que conservaban el RAG anterior.
                st.cache_resource.clear()

                st.rerun()

    st.divider()

 
    st.markdown("**🎭 Tono del asistente:**")

    tone_descriptions = {
        "Útil y amigable": (
            "Responde de manera clara, amable "
            "y fácil de entender."
        ),
        "Profesional y formal": (
            "Responde con un lenguaje serio, "
            "ordenado y académico."
        ),
        "Casual y relajado": (
            "Responde de forma natural, "
            "cercana y sencilla."
        ),
        "Experto técnico": (
            "Responde con mayor profundidad "
            "técnica y precisión."
        ),
        "Creativo y divertido": (
            "Responde usando ejemplos "
            "creativos y analogías."
        ),
    }

    selected_tone = st.selectbox(
        "Selecciona el tono del asistente",
        options=list(
            tone_descriptions.keys()
        ),
        index=list(
            tone_descriptions.keys()
        ).index(
            st.session_state.tono_asistente
        ),
        key="tone_selector",
    )

    st.session_state.tono_asistente = (
        selected_tone
    )

    st.info(
        tone_descriptions[selected_tone]
    )

    st.divider()


    st.markdown(
        "**🎓 Modo de aprendizaje:**"
    )

    learning_modes = {
        "Aprendizaje guiado": (
            "Te orientará mediante preguntas "
            "y pistas, sin entregar inmediatamente "
            "la solución."
        ),
        "Explicación conceptual": (
            "Explicará el tema, mostrará un ejemplo "
            "y comprobará tu comprensión."
        ),
        "Revisión de código": (
            "Analizará tu código y te ayudará "
            "a descubrir y corregir los errores."
        ),
        "Solución de referencia": (
            "Mostrará una solución completa "
            "con una explicación detallada."
        ),
    }

    selected_learning_mode = st.selectbox(
        "Selecciona cómo quieres aprender",
        options=list(
            learning_modes.keys()
        ),
        index=list(
            learning_modes.keys()
        ).index(
            st.session_state.modo_aprendizaje
        ),
        key="learning_mode_selector",
    )

    st.session_state.modo_aprendizaje = (
        selected_learning_mode
    )

    st.info(
        learning_modes[
            selected_learning_mode
        ]
    )

    st.divider()

    if st.button(
        "🗑️ Limpiar chat",
        type="secondary",
        use_container_width=True,
        key="clear_chat_button",
    ):
        st.session_state.messages = []
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
            "o consulta los resultados del diagnóstico."
        )

    for message in st.session_state.messages:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

            diagnostic_sources = (
                message.get(
                    "diagnostic_sources",
                    [],
                )
            )

            


with topics_column:
    st.markdown(
        "### 📚 Temas sugeridos"
    )

    st.info(
        """
        Puedes preguntar:

        - ¿Cuál es la principal dificultad del grupo?
        - ¿Cuántos estudiantes sienten frustración?
        - ¿Qué prefieren los estudiantes al aprender?
        - ¿Qué es una variable?
        - ¿Qué es un ciclo `for`?
        - ¿Cómo funciona un `if`?
        - Explícame las listas en Python.
        - Ayúdame a corregir este código.
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
        response, diagnostic_sources = (
            ask_assistant(
                question=user_input,
                tono=(
                    st.session_state
                    .tono_asistente
                ),
                modo_aprendizaje=(
                    st.session_state
                    .modo_aprendizaje
                ),
            )
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "diagnostic_sources": (
                diagnostic_sources
            ),
        }
    )

    st.rerun()



st.divider()

st.markdown(
    """
    <div style="text-align: center; color: #777;">
        💻 Asistente educativo con RAG diagnóstico
    </div>
    """,
    unsafe_allow_html=True,
)