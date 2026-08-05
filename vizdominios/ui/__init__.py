"""Capa de interfaz Streamlit: tema, barra lateral y pestanas de la practica."""

from __future__ import annotations

from .sidebar import Selection, render_sidebar
from .tabs import render_tabs
from .theme import inject_css, page_header, setup_page

__all__ = [
    "Selection",
    "inject_css",
    "page_header",
    "render_sidebar",
    "render_tabs",
    "setup_page",
]
