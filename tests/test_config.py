import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VARIABLES = ['APP_ENV', 'MEMORY_DB_PATH', 'OPENAI_MODEL', 'MODEL_TEMPERATURE',
             'MAX_HISTORY_MESSAGES', 'MODEL_TIMEOUT_SECONDS', 'MODEL_MAX_RETRIES',
             'MODEL_MAX_TOKENS', 'OPENAI_API_KEY']


class ConfigTests(unittest.TestCase):
    def run_config(self, overrides=None, dotenv='', code=None):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'Models').mkdir()
            shutil.copy(ROOT / 'Models/config.py', root / 'Models/config.py')
            (root / '.env').write_text(dotenv)
            env = {key: value for key, value in os.environ.items() if key not in VARIABLES}
            env.update(overrides or {})
            env['PYTHONPATH'] = str(root)
            return subprocess.run([sys.executable, '-c', code or
                'from Models.config import *; print(APP_ENV, MODEL_NAME, MEMORY_DB_PATH.name)'],
                cwd=root, env=env, text=True, capture_output=True)

    def test_development_retains_existing_database(self):
        result = self.run_config()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('development gpt-4o-mini conversation_memory.sqlite', result.stdout)

    def test_environment_overrides_dotenv(self):
        result = self.run_config({'OPENAI_MODEL': 'environment-model'}, 'OPENAI_MODEL=file-model\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('environment-model', result.stdout)

    def test_production_requires_absolute_persistent_path(self):
        for path in ['', 'data/test.sqlite']:
            result = self.run_config({'APP_ENV': 'production', 'MEMORY_DB_PATH': path})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('ruta absoluta', result.stderr)
        result = self.run_config({'APP_ENV': 'production', 'MEMORY_DB_PATH': '/tmp/test.sqlite'})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_numeric_values_do_not_echo_input(self):
        for key, value in [('MODEL_TEMPERATURE', 'NaN'), ('MODEL_TEMPERATURE', '3'),
                           ('MAX_HISTORY_MESSAGES', '1'), ('MODEL_MAX_RETRIES', 'secret-value'),
                           ('MODEL_TIMEOUT_SECONDS', '0'), ('MODEL_MAX_TOKENS', '999999')]:
            result = self.run_config({key: value})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(key, result.stderr)
            self.assertNotIn('secret-value', result.stderr)

    def test_missing_api_key_fails_without_printing_secret(self):
        result = self.run_config(code='from Models.config import validate_api_key; validate_api_key()')
        self.assertNotEqual(result.returncode, 0)
        result = self.run_config({'OPENAI_API_KEY': 'local-test-placeholder'},
                                code='from Models.config import validate_api_key; validate_api_key()')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('local-test-placeholder', result.stdout + result.stderr)

    def test_user_error_does_not_expose_exception(self):
        from UI.asistente import ask_assistant
        with patch('UI.asistente.initialize_system', side_effect=RuntimeError('secret-token-private-path')):
            with self.assertLogs('UI.asistente', level='ERROR') as logs:
                response, _ = ask_assistant('hola', 'Normal', 'Guiado', 'test')
        self.assertIn('Referencia:', response)
        self.assertNotIn('secret-token-private-path', response + str(logs.output))


if __name__ == '__main__':
    unittest.main()
