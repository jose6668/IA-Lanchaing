# Documentacion del Codigo

## 1. Descripcion general

El proyecto implementa un asistente educativo de programacion con una interfaz en Streamlit y un flujo RAG basado en LangChain. Su objetivo es apoyar a estudiantes mediante respuestas pedagogicas adaptadas al tono y modo de aprendizaje seleccionados.

Cuando la pregunta del usuario esta relacionada con el diagnostico educativo, el sistema recupera informacion desde un PDF indexado en ChromaDB. Cuando la pregunta es de programacion general, el prompt instruye al modelo para responder sin mencionar el diagnostico.

Tecnologias principales:

| Tecnologia | Uso |
| --- | --- |
| Python | Lenguaje principal del proyecto. |
| Streamlit | Interfaz web, chat y estado de sesion. |
| LangChain / LCEL | Composicion de la cadena del asistente. |
| langchain-openai | Integracion con `ChatOpenAI` y `OpenAIEmbeddings`. |
| ChromaDB | Base vectorial local y persistente. |
| PyPDFLoader | Carga del PDF diagnostico. |
| RecursiveCharacterTextSplitter | Fragmentacion del documento en chunks. |

## 2. Estructura actual

```text
IA-Lanchaing/
|-- app.py
|-- README.md
|-- chroma_diagnostico/
|-- docs/
|   `-- Reporte_Ejecutivo_Encuesta_Programacion.pdf
|-- Documentacion/
|   |-- ARQUITECTURA_PROYECTO.md
|   `-- DOCUMENTACION_CODIGO.md
|-- HU-docs/
|-- Models/
|   `-- config.py
|-- Prompts/
|   `-- prompt.py
|-- Services/
|   |-- diagnostic_rag.py
|   |-- ejemplo_Asistente_IA.py
|   `-- setup_diagnostic_rag.py
`-- UI/
    `-- asistente.py
```

## 3. Punto de entrada

```bash
streamlit run app.py
```

Flujo general:

1. `app.py` configura la pagina.
2. Inicializa `st.session_state.messages`, `tono_asistente` y `modo_aprendizaje`.
3. Renderiza sidebar, chat y temas sugeridos.
4. Permite reconstruir el diagnostico con `DiagnosticDocumentProcessor.setup()`.
5. Recibe preguntas con `st.chat_input`.
6. Llama a `ask_assistant()` desde `UI/asistente.py`.
7. Guarda respuesta y fuentes recuperadas.
8. Ejecuta `st.rerun()`.

## 4. Documentacion por modulo

### `app.py`

Responsabilidad: manejar la interfaz de usuario.

Funciones locales:

| Funcion | Descripcion |
| --- | --- |
| `diagnostic_is_configured()` | Verifica si existe la ruta de Chroma configurada. |
| `configure_diagnostic()` | Ejecuta el procesamiento del PDF y reconstruye la base vectorial. |

Estado de sesion:

| Clave | Uso |
| --- | --- |
| `messages` | Historial de mensajes del chat. |
| `tono_asistente` | Tono seleccionado por el usuario. |
| `modo_aprendizaje` | Modo pedagogico seleccionado. |

Observaciones:

- Usa imports wildcard.
- La UI incluye textos con problemas de codificacion.
- Solo valida existencia de carpeta Chroma, no integridad de coleccion.

### `UI/asistente.py`

Responsabilidad: coordinar la cadena conversacional.

| Funcion | Retorno | Descripcion |
| --- | --- | --- |
| `initialize_system()` | `(chain, diagnostic_rag)` | Crea `ChatOpenAI`, `PromptTemplate`, cadena LCEL y `DiagnosticRAG`. Usa cache de Streamlit. |
| `ask_assistant(question, tono, modo_aprendizaje)` | `(response, diagnostic_sources)` | Limpia la pregunta, recupera contexto, invoca la cadena y maneja errores. |
| `get_assistant_info()` | `dict` | Devuelve metadatos del asistente para la UI. |

Cadena LCEL:

```python
prompt_template | llm | StrOutputParser()
```

### `Services/diagnostic_rag.py`

Responsabilidad: recuperar informacion del diagnostico educativo desde ChromaDB.

Funciones auxiliares:

| Funcion | Descripcion |
| --- | --- |
| `normalize_text(text)` | Convierte a minusculas y elimina tildes. |
| `is_diagnostic_question(question)` | Detecta consultas relacionadas con diagnostico, encuesta, reporte o grupo. |
| `is_summary_question(question)` | Detecta solicitudes de resumen. |
| `main()` | Ejecuta pruebas manuales por consola. |

Metodos de `DiagnosticRAG`:

| Metodo | Descripcion |
| --- | --- |
| `__init__(chroma_path)` | Valida existencia de Chroma e inicializa embeddings y vectorstore. |
| `count_documents()` | Cuenta fragmentos almacenados. |
| `get_all_documents()` | Recupera todos los documentos para resumenes. Actualmente tiene un bug de indentacion. |
| `build_search_query(question)` | Construye una consulta enriquecida y define el tipo. |
| `retrieve(question)` | Recupera documentos segun tipo de consulta. |
| `format_context(documents)` | Convierte documentos recuperados en texto para el prompt. |
| `build_sources(documents)` | Deduplica fuentes por archivo y pagina. |
| `get_context(question)` | API principal usada por `ask_assistant()`. |


### `Services/setup_diagnostic_rag.py`

Responsabilidad: construir la base vectorial del diagnostico.

| Metodo | Descripcion |
| --- | --- |
| `validate_pdf()` | Verifica que el archivo exista y sea `.pdf`. |
| `load_document()` | Carga paginas con `PyPDFLoader` y agrega metadata. |
| `split_documents(documents)` | Divide paginas en chunks con overlap. |
| `remove_existing_vectorstore()` | Elimina el indice anterior para evitar duplicados. |
| `create_vectorstore(chunks)` | Crea la coleccion Chroma desde los chunks. |
| `setup()` | Ejecuta el flujo completo. |

Parametros de chunking:

| Parametro | Valor |
| --- | --- |
| `chunk_size` | `700` |
| `chunk_overlap` | `120` |
| `length_function` | `len` |

### `Models/config.py`

Responsabilidad: centralizar configuracion.

| Constante | Valor |
| --- | --- |
| `MODEL_NAME` | `gpt-4o-mini` |
| `EMBEDDINGS_MODEL` | `text-embedding-3-small` |
| `TEMPERATURE` | `0.3` |
| `RETRIEVAL_K` | `2` |
| `DIAGNOSTIC_COLLECTION_NAME` | `student_diagnostic` |

Riesgo actual:

`BASE_DIR = Path(__file__).resolve().parent` apunta a la carpeta `Models`. Por eso `DOCS_DIR` queda como `Models/docs` y `DIAGNOSTIC_CHROMA_PATH` queda como `Models/chroma_diagnostico`.

Para alinear rutas con la raiz del proyecto:

```python
BASE_DIR = Path(__file__).resolve().parent.parent
```

Tambien existe `from docs import *`, que no se usa y puede producir errores si no existe un paquete Python llamado `docs`.

### `Prompts/prompt.py`

Responsabilidad: definir `PROGRAMMING_TEMPLATE`.

Variables requeridas:

| Variable | Descripcion |
| --- | --- |
| `tono` | Estilo de comunicacion seleccionado. |
| `modo_aprendizaje` | Estrategia pedagogica seleccionada. |
| `tipo_consulta` | Puede ser `diagnostico` o `programacion`. |
| `contexto_diagnostico` | Fragmentos recuperados desde ChromaDB. |
| `question` | Pregunta del usuario. |

### `Services/ejemplo_Asistente_IA.py`

Responsabilidad: ejemplo o version previa del asistente.

Observaciones:

- No esta importado por `app.py`.
- Define funciones con errores tipograficos: `ask_assistent()` y `get_assitent_info()`.
- Invoca `PROGRAMMING_TEMPLATE` sin enviar `tipo_consulta` ni `contexto_diagnostico`.
- Si se ejecuta con el prompt actual, puede fallar por variables faltantes.

## 5. Comandos utiles

Procesar o reconstruir el diagnostico:

```bash
python -m Services.setup_diagnostic_rag
```

Ejecutar la aplicacion:

```bash
streamlit run app.py
```

Probar recuperacion RAG por consola:

```bash
python -m Services.diagnostic_rag
```

## 6. Pruebas recomendadas

- `normalize_text()` elimina tildes correctamente.
- `is_diagnostic_question()` clasifica preguntas del diagnostico.
- `is_summary_question()` detecta resumenes.
- `get_all_documents()` devuelve todos los chunks.
- `diagnostic_is_configured()` valida que la coleccion tenga documentos.
- `ask_assistant()` responde adecuadamente ante pregunta vacia.
- `ask_assistant()` maneja base vectorial inexistente.

## 7. Hallazgos y mejoras recomendadas

| Prioridad | Hallazgo | Recomendacion |
| --- | --- | --- |
| Alta | `Models/config.py` apunta rutas hacia `Models/` en lugar de la raiz. | Usar `Path(__file__).resolve().parent.parent`. |
| Alta | `get_all_documents()` retorna dentro del `for`. | Mover `sort()` y `return` fuera del ciclo. |
| Alta | `Services/ejemplo_Asistente_IA.py` no coincide con el prompt actual. | Actualizarlo o retirarlo. |
| Media | Hay textos con codificacion incorrecta. | Guardar archivos como UTF-8 y corregir literales. |
| Media | No hay archivo de dependencias. | Crear `requirements.txt` o `pyproject.toml`. |
| Media | No hay pruebas. | Agregar suite minima con `pytest`. |
| Baja | Imports wildcard. | Reemplazar por imports explicitos. |
