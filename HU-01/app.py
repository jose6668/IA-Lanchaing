

import streamlit as st
from ejemplo_Asistente_IA import *

st.set_page_config(
    page_title="Asistente de Programación",
    page_icon="💻",
    layout="wide"
)

st.title("💻 Asistente para Aprender Programación")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "tono_asistente" not in st.session_state:
    st.session_state.tono_asistente = "Útil y amigable"

with st.sidebar:
    st.header("📋 Información del Sistema")

    assistant_info = get_assitent_info()

    st.markdown("**🤖 Tipo de asistente:**")
    st.info(assistant_info["tipo"])

    st.markdown("**🧠 Modelo:**")
    st.info(assistant_info["modelo"])

    st.markdown("**🔥 Temperatura:**")
    st.info(str(assistant_info["temperatura"]))

    st.divider()

    st.markdown("**🎭 Tono del chatbot:**")

    tono_opcion = st.selectbox(
        "Selecciona el tono del asistente",
        [
            "Útil y amigable",
            "Profesional y formal",
            "Casual y relajado",
            "Experto técnico",
            "Creativo y divertido"
        ],
        index=[
            "Útil y amigable",
            "Profesional y formal",
            "Casual y relajado",
            "Experto técnico",
            "Creativo y divertido"
        ].index(st.session_state.tono_asistente)
    )

    st.session_state.tono_asistente = tono_opcion

    tonos_descripcion = {
        "Útil y amigable": "Responde de manera clara, amable y fácil de entender.",
        "Profesional y formal": "Responde con un lenguaje serio, ordenado y académico.",
        "Casual y relajado": "Responde de forma natural, cercana y sencilla.",
        "Experto técnico": "Responde con mayor profundidad técnica y precisión.",
        "Creativo y divertido": "Responde usando ejemplos creativos, analogías y un tono alegre."
    }

    st.info(tonos_descripcion[st.session_state.tono_asistente])

    st.divider()

    if st.button("🗑️ Limpiar Chat", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 💬 Chat de aprendizaje")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

with col2:
    st.markdown("### 📚 Temas sugeridos")

    st.info("""
Puedes preguntar sobre:

- ¿Qué es una variable?
- ¿Qué es un ciclo for?
- ¿Cómo funciona un if?
- Explícame listas en Python
- Dame ejercicios de lógica
- Corrige este código
- Explícame HTML y CSS
""")

if prompt := st.chat_input("Escribe tu pregunta sobre programación..."):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.spinner("💻 Analizando tu pregunta..."):
        response = ask_assistent(
            prompt,
            st.session_state.tono_asistente
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

    st.rerun()

st.divider()

st.markdown(
    "<div style='text-align: center; color: #666;'>💻 Asistente educativo para aprender programación</div>",
    unsafe_allow_html=True
)