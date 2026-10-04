"""Local preflight: no network requests, no secret output, no database migration."""
import os
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    try:
        from Models.config import APP_ENV, MEMORY_DB_PATH, ConfigurationError, validate_api_key
        validate_api_key()
        parent = MEMORY_DB_PATH.parent
        if not parent.is_dir():
            raise ConfigurationError('El directorio de MEMORY_DB_PATH no existe. Créalo con permisos para el usuario de la app.')
        with TemporaryFile(dir=parent):
            pass
        if MEMORY_DB_PATH.exists():
            if not MEMORY_DB_PATH.is_file() or not os.access(MEMORY_DB_PATH, os.W_OK):
                raise ConfigurationError('La base de datos no es un archivo escribible por el usuario de la app.')
            with sqlite3.connect(MEMORY_DB_PATH.resolve().as_uri() + '?mode=ro', uri=True) as connection:
                if connection.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ConfigurationError('La base de datos necesita revisión de integridad.')
        print(f'Configuración válida ({APP_ENV}). Almacenamiento accesible.')
        print('La clave está configurada; no se ha comprobado su validez con el proveedor.')
        print('Pendiente antes del acceso público: hashes de contraseñas, límites por usuario, HTTPS y respaldos.')
        return 0
    except Exception as error:
        # Only explicitly safe configuration messages may be printed.
        if type(error).__name__ == 'ConfigurationError':
            print(f'Configuración incompleta: {error}', file=sys.stderr)
        else:
            print('No se pudo comprobar la configuración. Revisa dependencias, rutas y permisos.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
