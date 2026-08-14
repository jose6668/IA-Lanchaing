# Documentacion del Codigo

## 1. Descripcion general

El proyecto implementa un asistente educativo de programacion con interfaz en Streamlit, orquestacion mediante LangGraph, clasificacion de consultas con un LLM y memoria conversacional persistente por sesion.

El objetivo pedagogico principal es el aprendizaje guiado. El asistente orienta al estudiante paso a paso, explica el razonamiento, ofrece pistas progresivas y evita entregar respuestas finales o codigo completo de inmediato.

Tecnologias principales:

| Tecnologia | Uso |
| --- | --- |
| Python | Lenguaje principal del proyecto. |
| Streamlit | Interfaz web, chat, tema visual y estado de sesion. |
| LangGraph | Orquestacion del flujo mediante nodos y estado compartido. |
| LangChain / LCEL | Composicion de prompts, modelo y parser. |
| langchain-openai | Integracion con `ChatOpenAI`. |
| RunnableWithMessageHistory | Memoria conversacional por `session_id`. |
| SQLite | Persistencia local del historial reciente. |

## 2. Estructura actual

```text
IA-Lanchaing/
|-- app.py
|-- README.md
|-- Documentacion/
|   |-- ARQUITECTURA_PROYECTO.md
|   `-- DOCUMENTACION_CODIGO.md
|-- Graphs/
|   |-- __init__.py
|   `-- learning_graph.py
|-- HU-docs/
|   |-- HU-001 - Asistente educativo de programacion con seleccion de tono.md
|   |-- HU_04.md
|   `-- HU_05.md
|-- Models/
|   `-- config.py
|-- Prompts/
|   `-- prompt.py
|-- Requirements/
|   `-- requirements.txt
|-- Services/
|   `-- ejemplo_Asistente_IA.py
`-- UI/
    `-- asistente.py
```

## 3. Punto de entrada

```bash
streamlit run app.py
```

Flujo general:

1. `app.py` configura la pagina.
2. Inicializa `st.session_state.messages`.
3. Inicializa `st.session_state.session_id`.
4. Renderiza sidebar, chat y temas sugeridos.
5. Recibe preguntas con `st.chat_input`.
6. Llama a `ask_assistant()` desde `UI/asistente.py`.
7. `ask_assistant()` invoca `LearningAssistantGraph`.
8. El grafo clasifica la consulta con un LLM.
9. LangGraph enruta hacia el nodo correspondiente.
10. La respuesta se genera con memoria conversacional.
11. Streamlit guarda la respuesta en el historial visual.

## 4. `app.py`

Responsabilidad: manejar la interfaz de usuario, aplicar el tema visual y enviar consultas al asistente.

Elementos relevantes:

| Elemento | Descripcion |
| --- | --- |
| `st.set_page_config()` | Configura titulo, icono y layout. |
| CSS con `st.markdown()` | Aplica el estilo visual de la aplicacion. |
| `st.session_state.messages` | Guarda el historial visible del chat. |
| `st.session_state.session_id` | Identifica la memoria conversacional de la sesion. |
| `st.query_params["session_id"]` | Conserva el identificador en la URL para recuperar la sesion. |
| `DEFAULT_ASSISTANT_TONE` | Tono fijo enviado al grafo. |
| `DEFAULT_LEARNING_MODE` | Modo pedagogico fijo enviado al grafo. |

Cuando el usuario limpia el chat, tambien se genera un nuevo `session_id`. Esto evita mezclar la nueva conversacion con el historial persistente anterior.

## 5. `UI/asistente.py`

Responsabilidad: adaptar la interfaz Streamlit al grafo de LangGraph.

| Funcion | Retorno | Descripcion |
| --- | --- | --- |
| `initialize_system()` | `LearningAssistantGraph` | Crea y cachea el grafo del asistente. |
| `ask_assistant(question, tono, modo_aprendizaje, session_id)` | `(response, [])` | Limpia la pregunta, invoca el grafo y devuelve la respuesta. |
| `get_assistant_info()` | `dict` | Devuelve metadatos publicos del asistente. |
| `get_recent_conversation(session_id)` | `list[dict]` | Recupera mensajes persistidos para reconstruir el chat visible. |

Manejo de errores:

- Pregunta vacia: devuelve una respuesta amable solicitando una pregunta.
- Error general: captura la excepcion, registra el error y devuelve un mensaje tecnico controlado.

## 6. `Graphs/learning_graph.py`

Responsabilidad: orquestar el flujo del asistente educativo con LangGraph.

Elementos principales:

| Elemento | Tipo | Descripcion |
| --- | --- | --- |
| `VALID_CATEGORIES` | `set[str]` | Categorias permitidas por el clasificador. |
| `LearningAssistantState` | `TypedDict` | Estado compartido entre nodos. |
| `LearningAssistantGraph` | Clase | Construye modelo, cadenas, memoria y grafo compilado. |
| `create_learning_assistant_graph()` | Funcion | Factory usada por `UI/asistente.py`. |

### Estado

| Campo | Descripcion |
| --- | --- |
| `question` | Pregunta del usuario. |
| `session_id` | Identificador de memoria conversacional. |
| `tono` | Tono de respuesta. |
| `modo_aprendizaje` | Estrategia pedagogica. |
| `tipo_consulta` | Categoria detectada. |
| `respuesta` | Respuesta final del modelo. |
| `historial` | Trazas internas del flujo. |

### Nodos

| Nodo | Descripcion |
| --- | --- |
| `clasificar_consulta` | Usa un LLM para clasificar la pregunta. |
| `generar_respuesta_programacion` | Genera una respuesta guiada de programacion. |
| `generar_revision_codigo` | Guia la revision de codigo o errores. |
| `responder_con_historial` | Usa la memoria conversacional para responder. |
| `responder_restriccion` | Rechaza preguntas fuera de dominio de forma amable. |
| `respuesta_final` | Cierra el flujo. |

### Clasificador

El clasificador responde exclusivamente con una de estas categorias:

```text
programacion
revision_codigo
historial
restriccion
```

Si la respuesta del clasificador no coincide con una categoria valida, `_normalize_category()` usa `restriccion` como fallback.

### Memoria

La memoria se guarda mediante `Services/conversation_memory.py` y se consume desde el grafo con:

```python
self.memory_store: dict[str, SQLiteLimitedChatMessageHistory] = {}
```

Cada `session_id` tiene su propio historial. La cadena principal usa:

```python
RunnableWithMessageHistory(
    chain,
    self.get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)
```

El limite activo es de 20 mensajes por sesion. Este valor se define en `Models/config.py`.

## 7. `Services/conversation_memory.py`

Responsabilidad: manejar la memoria persistente local del asistente.

| Elemento | Descripcion |
| --- | --- |
| `SQLiteLimitedChatMessageHistory` | Implementa historial compatible con LangChain usando SQLite. |
| `messages` | Recupera mensajes ordenados por sesion. |
| `add_messages()` | Guarda nuevos mensajes y recorta el historial. |
| `clear()` | Elimina mensajes de una sesion. |
| `get_recent_messages_for_ui()` | Convierte mensajes persistidos al formato usado por Streamlit. |

Regla principal:

```text
Cada session_id conserva maximo 20 mensajes.
```

## 8. `Prompts/prompt.py`

Responsabilidad: definir `PROGRAMMING_TEMPLATE`.

El prompt contiene:

- Rol del asistente como docente y mentor de programacion.
- Tono.
- Modo de aprendizaje.
- Tipo de consulta.
- Reglas generales de aprendizaje guiado.
- Reglas para `programacion`.
- Reglas para `revision_codigo`.
- Reglas para `historial`.
- Reglas para `restriccion`.

El historial no se inserta como texto dentro del template. Se inyecta como mensajes reales usando `MessagesPlaceholder` desde `Graphs/learning_graph.py`.

## 9. `Models/config.py`

Responsabilidad: centralizar configuracion basica.

| Constante | Valor |
| --- | --- |
| `BASE_DIR` | Raiz del proyecto. |
| `MODEL_NAME` | `gpt-4o-mini` |
| `TEMPERATURE` | `0.3` |
| `MEMORY_DB_PATH` | Ruta local de SQLite para memoria conversacional. |
| `MAX_HISTORY_MESSAGES` | `20` |

## 10. `Requirements/requirements.txt`

Dependencias principales:

| Paquete | Uso |
| --- | --- |
| `streamlit` | Interfaz web. |
| `langchain` | Base de cadenas y abstracciones. |
| `langchain-core` | Prompts, parsers y memoria. |
| `langchain-openai` | Integracion con OpenAI. |
| `langgraph` | Orquestacion del flujo. |
| `openai` | Cliente OpenAI. |
| `tiktoken` | Tokenizacion. |

## 11. Comandos utiles

Ejecutar la aplicacion:

```bash
streamlit run app.py
```

Validar sintaxis de archivos principales:

```bash
python -m py_compile app.py Graphs/learning_graph.py UI/asistente.py Models/config.py Prompts/prompt.py
```

Buscar referencias eliminadas:

```bash
rg "diagnost|RAG|Chroma|PDF|embedding|pypdf" app.py Graphs UI Models Prompts Requirements
```

## 12. Estado actual del codigo

Implementado:

- Grafo con cuatro rutas principales.
- Clasificacion con LLM.
- Memoria persistente por sesion.
- Limite de 20 mensajes por sesion.
- Restriccion fuera de dominio.
- Eliminacion de dependencias de RAG.

Pendiente recomendado:

- Pruebas automatizadas del grafo.
- Streaming de respuestas.
- Persistencia real de memoria cuando se avance a bases de datos.
