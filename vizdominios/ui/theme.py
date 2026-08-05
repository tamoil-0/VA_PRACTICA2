"""Configuracion de pagina, CSS y encabezado de la aplicacion Streamlit."""

from __future__ import annotations

import streamlit as st

from .. import config as cfg


def setup_page() -> None:
    """Configura titulo, icono y layout. Debe llamarse antes de cualquier widget."""
    st.set_page_config(
        page_title="Dominios geograficos - Practica 02",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_css() -> None:
    """Estilos propios: tarjetas de metricas, notas, respuestas y tablas."""
    st.markdown(
        f"""
        <style>
        :root {{
            --ink: {cfg.PALETTE["ink"]};
            --muted: {cfg.PALETTE["muted"]};
            --line: {cfg.PALETTE["line"]};
            --accent: {cfg.PALETTE["real"]};
            --generated: {cfg.PALETTE["generated"]};
            --mesh: {cfg.PALETTE["mesh"]};
        }}
        .stApp {{
            background: linear-gradient(180deg, #f8fbfd 0%, #eef5f7 45%, #f8faf8 100%);
            color: var(--ink);
        }}
        [data-testid="stSidebar"] {{
            background: #ffffff;
            border-right: 1px solid var(--line);
        }}
        h1, h2, h3 {{ color: var(--ink); letter-spacing: 0; }}
        h1 {{ font-size: clamp(1.9rem, 3.4vw, 3.2rem); line-height: 1.05; margin-bottom: .2rem; }}
        .hero {{
            padding: 1.1rem 0 1.4rem 0;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1rem;
        }}
        .hero p {{ max-width: 1000px; color: var(--muted); font-size: 1.02rem; line-height: 1.55; }}
        .badge-row {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .6rem; }}
        .badge {{
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: .18rem .7rem;
            font-size: .78rem;
            color: var(--muted);
        }}
        .metric-wrap [data-testid="stMetric"] {{
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: .85rem 1rem;
            box-shadow: 0 12px 30px rgba(19, 34, 56, .05);
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid var(--line);
            border-radius: 10px;
            overflow: hidden;
        }}
        .note {{
            border-left: 4px solid var(--accent);
            background: #ffffff;
            padding: .85rem 1rem;
            border-radius: 8px;
            color: #213547;
            margin: .5rem 0 1rem 0;
            line-height: 1.5;
        }}
        .answer {{
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 1rem 1.05rem;
            margin-bottom: .75rem;
            box-shadow: 0 10px 24px rgba(19, 34, 56, .04);
            line-height: 1.55;
        }}
        .answer b {{ color: var(--accent); }}
        .legend {{ display: flex; gap: 1.2rem; flex-wrap: wrap; margin: .3rem 0 .8rem 0; font-size: .85rem; color: var(--muted); }}
        .dot {{ display: inline-block; width: .68rem; height: .68rem; border-radius: 50%; margin-right: .35rem; }}
        .small-muted {{ color: var(--muted); font-size: .88rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header() -> None:
    """Encabezado con titulo, resumen y credenciales academicas."""
    st.markdown(
        f"""
        <div class="hero">
            <h1>Visualizacion de dominios geograficos</h1>
            <p>
                Puntos reales, cuadricula regular y malla visual sobre un dominio
                delimitado con coordenadas de latitud y longitud. La aplicacion recorre
                las siete actividades de la practica, calcula metricas de densidad y
                genera el informe PDF final.
            </p>
            <div class="badge-row">
                <span class="badge">{cfg.COURSE}</span>
                <span class="badge">{cfg.PRACTICE_TITLE}</span>
                <span class="badge">{cfg.UNIT}</span>
                <span class="badge">Estudiante: {cfg.STUDENT_NAME}</span>
                <span class="badge">Dataset: {cfg.DATASET_NAME}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def color_legend() -> None:
    """Leyenda de la codificacion visual usada en todo el proyecto."""
    st.markdown(
        f"""
        <div class="legend">
            <span><span class="dot" style="background:{cfg.PALETTE['real']}"></span>Puntos reales (dataset)</span>
            <span><span class="dot" style="background:{cfg.PALETTE['generated']}"></span>Puntos generados (cuadricula)</span>
            <span><span class="dot" style="background:{cfg.PALETTE['mesh']}"></span>Lineas de la malla</span>
            <span><span class="dot" style="background:{cfg.PALETTE['ink']}"></span>Limite del dominio D</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def note(text: str) -> None:
    """Bloque destacado de interpretacion."""
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


def answer_card(title: str, body: str) -> None:
    """Tarjeta de pregunta y respuesta."""
    st.markdown(f'<div class="answer"><b>{title}</b><br>{body}</div>', unsafe_allow_html=True)
