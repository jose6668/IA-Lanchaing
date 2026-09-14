"""Shared visual identity for authentication and the learning workspace."""
import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

ICON_PATH = Path(__file__).parent / "assets" / "tutor-icon.png"


@lru_cache(maxsize=1)
def icon_uri() -> str:
    return "data:image/png;base64," + base64.b64encode(ICON_PATH.read_bytes()).decode()


def brand() -> str:
    return f'<div class="brand"><img src="{icon_uri()}" alt="Icono del tutor"/><div><strong>Asistente de Programación</strong><small>Aprende · Practica · Construye</small></div></div>'


def apply_theme() -> None:
    st.markdown('<style>' + (Path(__file__).parent / 'theme.css').read_text() + '</style>', unsafe_allow_html=True)
