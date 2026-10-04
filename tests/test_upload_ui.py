import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class UploadUITests(unittest.TestCase):
    def test_submit_attachment_and_group_chat_actions(self):
        with TemporaryDirectory() as folder, patch('Models.config.MEMORY_DB_PATH', Path(folder) / 'test.sqlite'):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
            app.session_state.current_user = {'username': 'test_upload', 'name': 'Prueba'}
            app.run()
            self.assertFalse(app.exception)
            upload = BytesIO(b'print(42)')
            upload.name = 'example.py'
            submission = SimpleNamespace(text='Explica el archivo', files=[upload])
            with patch('streamlit.chat_input', side_effect=[submission, None]), patch('UI.asistente.ask_assistant', return_value=('Respuesta simulada', [])) as ask:
                app.run()
                self.assertFalse(app.exception)
                self.assertIn('print(42)', ask.call_args.kwargs['question'][1]['text'])
            self.assertTrue(app.session_state.current_chat_id)
            buttons = [b.key for b in app.sidebar.button]
            self.assertEqual(buttons.index('delete_chat_button'), buttons.index('clear_chat_button') + 1)
            app.button(key='clear_chat_button').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state.messages, [])
            app.button(key='delete_chat_button').click().run()
            self.assertFalse(app.exception)
            self.assertIsNone(app.session_state.current_chat_id)


if __name__ == '__main__':
    unittest.main()
