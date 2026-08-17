# HU-001 - Asistente educativo de programación con selección de tono

> Nota de actualizacion V04: esta HU documenta una etapa anterior del proyecto. En la version actual, la seleccion de tono fue retirada y el asistente usa un tono fijo `Normal, claro y amigable` para mantener una experiencia pedagogica consistente.

## 1. Resumen de la historia de usuario

Se implementó una funcionalidad para que un estudiante pueda interactuar con un asistente educativo de programación desde una interfaz web.

El asistente permite realizar preguntas sobre programación, seleccionar el tono de las respuestas y consultar explicaciones adaptadas para personas que están comenzando a aprender.

La aplicación mantiene el historial visual del chat durante la sesión y permite limpiar la conversación cuando el usuario lo necesite.

## 2. Objetivo funcional

Permitir que el usuario reciba apoyo para aprender programación mediante:

- Un chat educativo.
- Selección del tono del asistente.
- Explicaciones claras y paso a paso.
- Ejemplos sencillos de programación.
- Sugerencias de temas para estudiar.
- Respuestas generadas mediante un modelo de lenguaje.

## 3. Lo que se realizó

### Interfaz de usuario

Se creó una aplicación en Streamlit que incluye:

- Selector de tono del asistente.
- Descripción del tono seleccionado.
- Botón para limpiar el chat.
- Sección principal de conversación.
- Visualización del historial de mensajes.
- Campo para escribir preguntas.
- Indicador de carga mientras se genera la respuesta.
- Sección lateral con temas sugeridos.
- Mensaje informativo en la parte inferior de la aplicación.

Los tonos disponibles son:

- Útil y amigable.
- Profesional y formal.
- Casual y relajado.
- Experto técnico.
- Creativo y divertido.

### Gestión del estado conversacional

Se utiliza `st.session_state` para mantener:

- El historial de mensajes.
- El tono seleccionado por el usuario.

El tono elegido se guarda mediante:

```python
st.session_state.tono_asistente = tono_opcion
