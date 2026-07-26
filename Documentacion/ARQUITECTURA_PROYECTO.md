# Arquitectura del Proyecto

## 1. Descripcion general

El proyecto es una aplicacion web local construida con Streamlit que funciona como asistente educativo para aprender programacion. La version actual, V04, define una experiencia de aprendizaje guiado: el asistente no debe entregar respuestas completas de inmediato, sino orientar al estudiante paso a paso, explicar el razonamiento y detenerse para que el estudiante intente avanzar.

Ademas de responder preguntas generales de programacion, el asistente integra un flujo RAG sobre un documento PDF de diagnostico educativo. Cuando la consulta esta relacionada con la encuesta, el grupo, los estudiantes o el reporte, el sistema recupera fragmentos relevantes desde ChromaDB y los incorpora al prompt del modelo.

La aplicacion usa LangGraph como capa de orquestacion. Esto permite separar el proceso de respuesta en nodos: clasificacion de consulta, recuperacion diagnostica, generacion de respuesta, revision de codigo y respuesta final.

## 2. Alcance del sistema

Responsabilidades implementadas:

- Renderizar una interfaz de chat con Streamlit.
- Mantener un tono fijo: `Normal, claro y amigable`.
- Mantener un modo pedagogico fijo: `Aprendizaje guiado`.
- Aplicar una paleta visual personalizada en la interfaz.
- Procesar un PDF diagnostico mediante LangChain.
- Dividir el documento en fragmentos recuperables.
- Crear una base vectorial persistente en ChromaDB.
- Invocar un modelo de OpenAI para generar respuestas pedagogicas.
- Orquestar el flujo conversacional mediante LangGraph.
- Clasificar consultas como diagnostico, programacion o revision de codigo.
- Mantener historial de chat en `st.session_state`.
- Documentar dependencias en `Requirements/requirements.txt`.

Fuera del alcance actual:

- Autenticacion y autorizacion.
- API REST propia.
- Persistencia permanente del historial conversacional.
- Checkpointing de LangGraph.
- Human-in-the-loop.
- Agents o Tools de LangChain.
- Evaluaciones automaticas.
- Observabilidad avanzada con LangSmith.
- Despliegue cloud documentado.
- Pruebas automatizadas.

## 3. Decisiones arquitectonicas de la V04

| Decision | Justificacion |
| --- | --- |
| Quitar selector de tono | Reduce configuracion innecesaria y mantiene una voz consistente. |
| Usar tono fijo desde `app.py` | Evita modificar el grafo y mantiene compatibilidad con la firma existente. |
| Quitar selector de modo | Impide que el usuario seleccione un modo contrario al objetivo guiado. |
| Usar `Aprendizaje guiado` como constante | Convierte la intencion pedagogica en comportamiento por defecto del sistema. |
| Reforzar `PROGRAMMING_TEMPLATE` | La UI no basta para controlar el comportamiento del modelo; el prompt debe fijar reglas. |
| Aplicar paleta por CSS en `app.py` | Centraliza la personalizacion visual sin crear nuevos modulos ni dependencias. |
| Crear `Requirements/requirements.txt` | Hace reproducible la instalacion y evita depender del entorno local. |

## 4. Estilo arquitectonico

| Estilo | Aplica | Evidencia |
| --- | --- | --- |
| Monolito modular | Si | La aplicacion se ejecuta desde `app.py` y consume modulos internos. |
| Arquitectura por capas ligera | Si | `app.py` maneja UI, `UI/asistente.py` adapta Streamlit al grafo, `Graphs/` orquesta, `Services/` recupera y procesa datos. |
| RAG | Si | PDF -> chunks -> embeddings -> ChromaDB -> contexto -> LLM. |
| LCEL | Si | La generacion usa `PromptTemplate | ChatOpenAI | StrOutputParser`. |
| LangGraph | Si | `Graphs/learning_graph.py` define estado, nodos y rutas condicionales. |
| Theming local | Si | `app.py` inyecta CSS con la paleta visual de la V04. |
| Microservicios | No | No hay servicios separados ni comunicacion entre procesos. |

## 5. Componentes principales

| Componente | Archivo o carpeta | Responsabilidad |
| --- | --- | --- |
| Interfaz Streamlit | `app.py` | Renderiza pagina, sidebar, chat, controles de diagnostico, constantes pedagogicas y tema visual. |
| Adaptador del asistente | `UI/asistente.py` | Inicializa el grafo cacheado, procesa preguntas y devuelve respuesta/fuentes a Streamlit. |
| Grafo educativo | `Graphs/learning_graph.py` | Orquesta el flujo con LangGraph y separa nodos especializados. |
| Recuperacion RAG | `Services/diagnostic_rag.py` | Detecta consultas diagnosticas, consulta ChromaDB, formatea contexto y fuentes. |
| Procesador documental | `Services/setup_diagnostic_rag.py` | Carga el PDF, lo divide en chunks, genera embeddings y crea ChromaDB. |
| Configuracion | `Models/config.py` | Define rutas, modelos, temperatura, coleccion y cantidad de documentos recuperados. |
| Prompt | `Prompts/prompt.py` | Define reglas pedagogicas, guia paso a paso y comportamiento por tipo de consulta. |
| Dependencias | `Requirements/requirements.txt` | Lista las dependencias directas necesarias para instalar el proyecto. |
| Documento fuente | `docs/` | Contiene el PDF de diagnostico educativo. |
| Base vectorial | `chroma_diagnostico/` | Persistencia local de embeddings y fragmentos. |

## 6. Diagramas

### 6.1 Arquitectura de componentes

```mermaid
flowchart LR
    U[Usuario] --> APP[app.py Streamlit]
    APP --> THEME[CSS paleta V04]
    APP --> PED[Tono fijo y aprendizaje guiado fijo]
    PED --> UI[UI/asistente.py]
    UI --> GRAPH[Graphs/learning_graph.py]
    GRAPH --> OAI[OpenAI Chat API]
    GRAPH --> RAG[Services/diagnostic_rag.py]
    RAG --> CH[ChromaDB local]
    SETUP[Services/setup_diagnostic_rag.py] --> PDF[PDF diagnostico]
    SETUP --> EMB[OpenAI Embeddings API]
    SETUP --> CH
    RAG --> EMB
```

### 6.2 Flujo de LangGraph

```mermaid
flowchart TD
    APP[app.py] --> CONST[Constantes pedagogicas]
    CONST --> ASIS[UI/asistente.py]
    ASIS --> GRAPH[LearningAssistantGraph]
    GRAPH --> CLAS[clasificar_consulta]
    CLAS --> ROUTE{tipo_consulta}
    ROUTE -->|diagnostico| RAG[recuperar_diagnostico]
    ROUTE -->|programacion| PROG[generar_respuesta_programacion]
    ROUTE -->|revision_codigo| CODE[analizar_codigo]
    RAG --> DIAG[generar_respuesta_diagnostico]
    PROG --> FINAL[respuesta_final]
    CODE --> FINAL
    DIAG --> FINAL
```

### 6.3 Flujo pedagogico guiado

```mermaid
flowchart TD
    P[Pregunta del estudiante] --> A{Hay contexto suficiente?}
    A -->|No| Q[Pregunta clarificadora breve]
    A -->|Si| S1[Presentar primer paso]
    Q --> S1
    S1 --> R[Explicar razonamiento del paso]
    R --> T[Detenerse y pedir intento del estudiante]
    T --> H{Estudiante se atasca?}
    H -->|Si| PISTA[Ofrecer pista sutil]
    H -->|No| NEXT[Avanzar al siguiente paso]
```

## 7. Flujo principal de consulta

1. El usuario escribe una pregunta en Streamlit.
2. `app.py` usa `DEFAULT_ASSISTANT_TONE` y `DEFAULT_LEARNING_MODE`.
3. `app.py` llama a `ask_assistant()`.
4. `UI/asistente.py` inicializa o reutiliza `LearningAssistantGraph`.
5. El grafo crea un estado con pregunta, tono fijo, modo guiado, fuentes y respuesta.
6. `clasificar_consulta` decide si la consulta es de diagnostico, programacion o revision de codigo.
7. Si es diagnostico, `recuperar_diagnostico` consulta ChromaDB.
8. El nodo de generacion correspondiente invoca la cadena LCEL.
9. El prompt obliga al modelo a responder con aprendizaje guiado.
10. `respuesta_final` prepara el resultado.
11. Streamlit muestra la respuesta y conserva el historial en sesion.

## 8. Arquitectura de IA, LangChain y LangGraph

| Elemento | Valor actual |
| --- | --- |
| Proveedor | OpenAI |
| Modelo de chat | `gpt-4o-mini` |
| Modelo de embeddings | `text-embedding-3-small` |
| Temperatura | `0.3` |
| Reintentos de chat | `max_retries=2` |
| Recuperacion | `RETRIEVAL_K = 2` |
| Vector store | ChromaDB local |
| Framework UI | Streamlit |
| Orquestacion | LangGraph con `StateGraph` |
| Tono | Fijo desde `app.py` |
| Modo pedagogico | Fijo como `Aprendizaje guiado` |

Estado principal:

```python
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
```

La cadena de generacion se mantiene como LCEL:

```python
prompt_template | llm | StrOutputParser()
```

## 9. Arquitectura visual

La V04 incorpora una paleta visual aplicada desde `app.py` mediante CSS inyectado con `st.markdown`.

| Variable CSS | Color | Uso |
| --- | --- | --- |
| `--color-celeste` | `#95D1DC` | Bordes, mensajes y acentos suaves. |
| `--color-menta` | `#E7F0EA` | Fondo principal y sidebar. |
| `--color-azul` | `#1A77A3` | Titulos, botones y footer. |
| `--color-azul-oscuro` | `#155F82` | Hover de botones dentro de la misma gama cromatica. |
| `--color-superficie` | `#F7FBFA` | Fondo claro para app, header, contenedor inferior y entrada del chat. |
| `--color-texto` | `#173642` | Texto principal. |

Esta capa visual no modifica la logica de IA ni el flujo de LangGraph. Su responsabilidad es mejorar la legibilidad, identidad visual y consistencia de la experiencia. En el ajuste posterior de V04 se quitaron los acentos coral y amarillo de los elementos visibles para evitar contrastes innecesarios en la parte superior, en el contenedor inferior fijo y en la entrada del chat.

## 10. Riesgos tecnicos identificados

| Prioridad | Riesgo | Estado | Recomendacion |
| --- | --- | --- | --- |
| Media | Imports wildcard | Pendiente en `app.py`. | Usar imports explicitos. |
| Media | Validacion parcial de Chroma en sidebar | Pendiente. | Validar que la coleccion exista y tenga documentos. |
| Media | Falta de pruebas | Pendiente. | Agregar pruebas para nodos del grafo, clasificacion, RAG y reglas de prompt. |
| Media | CSS acoplado a `app.py` | Aceptado para V04. | Mover a archivo o helper si crece la interfaz. |
| Baja | Modulo legado incompatible | Pendiente. | Actualizar o retirar `Services/ejemplo_Asistente_IA.py`. |
| Baja | Fuentes RAG no visibles en el chat | Pendiente. | Renderizar `diagnostic_sources` debajo de respuestas diagnosticas. |

## 11. Evolucion por versiones

| Version | Enfoque |
| --- | --- |
| HU-001 | Chat educativo inicial con seleccion de tono. |
| HU-002 | Incorporacion de RAG diagnostico con ChromaDB. |
| HU-003 | Integracion de LangGraph para orquestar consultas. |
| HU-004 | Aprendizaje guiado fijo, tono fijo, paleta visual y dependencias. |
