# Preparación de producción — paso 1

Esta fase prepara configuración, dependencias y secretos. No publica la app ni configura un VPS. Se conserva el comportamiento de usuarios, chats y adjuntos.

## Requisitos y dependencias

Usar Python 3.12. Las dependencias directas están fijadas en `Requirements/requirements.txt`; `Requirements/requirements.lock.txt` incluye también las transitivas del entorno probado. Instalar desde la raíz:

```bash
python3.12 -m venv venv
venv/bin/python -m pip install -r Requirements/requirements.lock.txt
venv/bin/python -m pip check
```

El snapshot procede del entorno macOS actual. La instalación y ejecución en Linux se deben validar antes del despliegue. No es una auditoría de vulnerabilidades ni un lock con hashes. Al actualizar dependencias, hacerlo en un entorno aislado, ejecutar pruebas y regenerar el archivo completo; no actualizar automáticamente en cada arranque.

## Configuración privada

```bash
cp .env.example .env
chmod 600 .env
```

Editar `.env` localmente y añadir `OPENAI_API_KEY`. No pegar la clave en conversaciones, capturas o commits. `.env`, sus variantes, `.streamlit/secrets.toml`, bases de datos y respaldos quedan excluidos de Git. `.env.example` es la plantilla pública y no debe contener credenciales.

La app carga `.env` desde la raíz del proyecto, independientemente del directorio actual. Las variables ya definidas en el proceso tienen prioridad; no hay interpolación de valores. No se utiliza `secrets.toml` como fuente adicional, para mantener una sola configuración. En el VPS se podrán inyectar las mismas variables desde el gestor del servicio.

| Variable | Valor inicial | Uso |
| --- | --- | --- |
| `APP_ENV` | `development` | `development` o `production`. |
| `OPENAI_API_KEY` | Vacío | Clave privada del proveedor. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modelo compatible con los mensajes multimodales y parámetros del proyecto. |
| `MODEL_TEMPERATURE` | `0.3` | Número entre 0 y 2. |
| `MODEL_TIMEOUT_SECONDS` | `60` | Tiempo de espera de cada petición, entre 5 y 300 segundos. |
| `MODEL_MAX_RETRIES` | `2` | Reintentos por petición, entre 0 y 5. |
| `MODEL_MAX_TOKENS` | `1500` | Límite de salida por llamada, entre 64 y 8192. |
| `MAX_HISTORY_MESSAGES` | `20` | Mensajes conservados por chat, entre 2 y 100. |
| `MEMORY_DB_PATH` | Vacío en desarrollo | Ruta SQLite. En producción debe ser absoluta y persistente. |

Cambiar de modelo puede requerir otros parámetros del proveedor. Los límites de salida y tiempo no sustituyen cuotas por usuario ni un presupuesto de gasto. Cada consulta utiliza clasificación y respuesta, y cada petición puede reintentarse.

## Conservación de datos

En desarrollo, dejar `MEMORY_DB_PATH` vacío conserva la base `conversation_memory.sqlite` existente. En producción, configurar por ejemplo `/srv/ia-lanchaing/data/conversation_memory.sqlite` y crear el directorio con permisos de escritura para el usuario del servicio. La ruta es un ejemplo: no se crea automáticamente en este paso.

El directorio debe sobrevivir a los despliegues y, si se usa Docker, pertenecer a un volumen persistente. La configuración no copia ni migra datos. Apuntar a una ruta nueva inicia una base vacía; para trasladar datos habrá que detener la aplicación y realizar una copia SQLite consistente o usar su API de backup. No copiar una base activa sin un procedimiento de respaldo.

## Comprobación y arranque

```bash
venv/bin/python scripts/check_config.py
venv/bin/python scripts/run_app.py
```

La comprobación valida valores, presencia de clave, acceso al directorio y la integridad básica de una base existente. No imprime la clave, no realiza llamadas a la API y no modifica registros. La presencia de una clave no demuestra que sea válida ni que tenga saldo.

El arranque carga primero esa comprobación y después inicia Streamlit desde la raíz. Escucha únicamente en `127.0.0.1:8501`; no queda expuesto públicamente. Para uso local, abrir `http://localhost:8501`. Detener con Ctrl+C. Reiniciar el proceso después de editar Python, CSS, configuración o secretos, porque la recarga automática está desactivada.

Streamlit conserva las protecciones CORS y XSRF, limita los archivos a 5 MB y oculta detalles de excepciones. La aplicación muestra una referencia de error; su logger registra esa referencia y el tipo de excepción sin incluir el mensaje del proveedor. Revisar también la configuración de logs del servidor y de librerías antes de producción.

## Validación

```bash
venv/bin/python -m unittest discover -s tests -v
venv/bin/python -m pip check
git diff --check
```

Las pruebas cubren precedencia del entorno, valores inválidos, ruta obligatoria en producción, ausencia de clave, errores sin secretos, chats, adjuntos y memoria multimodal. No realizan llamadas reales al modelo.

## Requisitos aún pendientes antes de acceso público

- Reemplazar las contraseñas en texto plano por hashes seguros y migrar usuarios existentes con respaldo previo. Esta fase no altera la base de datos ni el esquema de usuarios.
- Limitar intentos de inicio de sesión, registro y consumo por usuario.
- Configurar servicio con reinicio, HTTPS, proxy, firewall y actualizaciones del VPS.
- Preparar respaldos externos y probar su restauración.
- Probar instalación Linux, concurrencia y consumo con documentos e imágenes reales.

Pasar la comprobación de configuración no significa que la app ya esté lista para abrirse al público.
