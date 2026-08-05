"""Pestanas de la aplicacion: una por actividad de la practica.

Cada funcion ``_tab_*`` recibe el ``AnalysisResult`` y solo se encarga de
presentar informacion; todo el calculo ya viene resuelto por ``pipeline`` y
``analysis``, y todos los textos vienen de ``content``. Asi la interfaz no
duplica logica ni redacta interpretaciones propias.
"""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from .. import charts, config as cfg, content, maps
from ..analysis import (
    coordinate_summary,
    nearest_neighbor_km,
    real_vs_generated,
    resolution_sensitivity,
)
from ..dataio import column_profile, dataset_overview, to_geojson
from ..pipeline import AnalysisResult
from ..report import build_report
from .theme import answer_card, color_legend, note

TAB_LABELS = [
    "Resumen",
    "Mapa real",
    "1. Exploracion",
    "2. Limpieza",
    "3. Dominio",
    "4-6. Visualizaciones",
    "Analisis extra",
    "7. Interpretacion",
    "Informe PDF",
    "Codigo",
]


def render_tabs(result: AnalysisResult) -> None:
    """Dibuja las metricas superiores y todas las pestanas."""
    _metric_row(result)
    tabs = st.tabs(TAB_LABELS)
    renderers = [
        _tab_summary,
        _tab_map,
        _tab_exploration,
        _tab_cleaning,
        _tab_domain,
        _tab_visualizations,
        _tab_extra_analysis,
        _tab_interpretation,
        _tab_report,
        _tab_code,
    ]
    for tab, renderer in zip(tabs, renderers):
        with tab:
            renderer(result)


def _metric_row(result: AnalysisResult) -> None:
    """Tarjetas con las cifras clave del analisis actual."""
    st.markdown('<div class="metric-wrap">', unsafe_allow_html=True)
    highlights = content.numeric_highlights(result)
    for row_start in (0, 4):
        cols = st.columns(4)
        for col, (label, value) in zip(cols, highlights[row_start : row_start + 4]):
            col.metric(label, value)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------
def _tab_summary(result: AnalysisResult) -> None:
    st.subheader("Trazabilidad de las siete actividades")
    st.caption(
        "Cada linea es el resultado real del analisis en curso, recalculado con "
        "el pais, los filtros y los valores de dx/dy seleccionados."
    )
    for line in result.summary_lines():
        st.markdown(f"- {line}")

    color_legend()

    st.subheader("Verificacion de la rubrica")
    rubric = pd.DataFrame(
        content.rubric_rows(result),
        columns=["Criterio de evaluacion", "Puntaje", "Evidencia en este trabajo"],
    )
    st.dataframe(rubric, width="stretch", hide_index=True)
    note(
        f"Los {cfg.TOTAL_POINTS} puntos de la rubrica estan cubiertos: exploracion, "
        "limpieza, dominio, puntos reales, cuadricula, malla e interpretacion, mas "
        "el informe PDF y el codigo como productos entregables."
    )


# ---------------------------------------------------------------------------
# Mapa real
# ---------------------------------------------------------------------------
def _tab_map(result: AnalysisResult) -> None:
    st.subheader("Las tres visualizaciones sobre cartografia real")
    st.caption(
        "Valor agregado: proyectar puntos, cuadricula y malla sobre OpenStreetMap "
        "permite comprobar que el dominio calculado coincide con el territorio."
    )
    map_tabs = st.tabs(["Localidades y dominio", "Cuadricula en el mapa", "Malla en el mapa"])
    with map_tabs[0]:
        st.plotly_chart(
            maps.map_points(result.clean, result.domain, result.country),
            width="stretch",
        )
    with map_tabs[1]:
        st.plotly_chart(
            maps.map_grid(result.clean, result.grid, result.country),
            width="stretch",
        )
        st.caption(
            f"{result.grid.size:,} nodos generados con dx = {result.dx} y dy = {result.dy} "
            "dentro del dominio, junto a los puntos reales."
        )
    with map_tabs[2]:
        st.plotly_chart(
            maps.map_mesh(result.clean, result.grid, result.country),
            width="stretch",
        )
        st.caption(
            f"{result.grid.ny} lineas horizontales y {result.grid.nx} verticales "
            f"forman {result.grid.cells:,} celdas sobre el territorio."
        )


# ---------------------------------------------------------------------------
# Actividad 1
# ---------------------------------------------------------------------------
def _tab_exploration(result: AnalysisResult) -> None:
    st.subheader("Actividad 1. Exploracion de la base de datos")
    note(content.dataset_description(result))

    st.markdown("**Respuestas de la actividad**")
    st.dataframe(
        dataset_overview(result.raw, result.columns),
        width="stretch",
        hide_index=True,
    )

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Perfil de columnas**")
        st.dataframe(column_profile(result.raw), width="stretch", hide_index=True)
    with right:
        st.markdown("**Rol de cada columna en la practica**")
        st.dataframe(result.columns.as_table(), width="stretch", hide_index=True)

    st.markdown("**Primeras filas del archivo original**")
    st.dataframe(result.raw.head(20), width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Actividad 2
# ---------------------------------------------------------------------------
def _tab_cleaning(result: AnalysisResult) -> None:
    st.subheader("Actividad 2. Limpieza y seleccion de datos")
    note(
        f"Filtro de pais ({result.country}), conversion de coordenadas a numerico, "
        "eliminacion de nulos, descarte de coordenadas fuera de rango y eliminacion "
        f"de duplicados. Resultado: <b>{len(result.clean):,}</b> localidades validas."
    )

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Auditoria de la limpieza**")
        st.dataframe(result.cleaning.as_table(), width="stretch", hide_index=True)
    with right:
        st.markdown("**Estadisticos de las coordenadas**")
        st.dataframe(coordinate_summary(result.clean), width="stretch", hide_index=True)

    st.markdown("**Tabla limpia con los datos geograficos**")
    st.dataframe(result.clean, width="stretch", hide_index=True)

    csv = result.clean.to_csv(index=False).encode("utf-8")
    geojson = json.dumps(to_geojson(result.clean), ensure_ascii=False, indent=2).encode("utf-8")
    col1, col2 = st.columns(2)
    col1.download_button(
        "Descargar tabla limpia (CSV)",
        data=csv,
        file_name="tabla_limpia.csv",
        mime="text/csv",
        width="stretch",
    )
    col2.download_button(
        "Descargar puntos (GeoJSON)",
        data=geojson,
        file_name="localidades.geojson",
        mime="application/geo+json",
        width="stretch",
    )


# ---------------------------------------------------------------------------
# Actividad 3
# ---------------------------------------------------------------------------
def _tab_domain(result: AnalysisResult) -> None:
    domain = result.domain
    st.subheader("Actividad 3. Delimitacion del dominio geografico")
    st.latex(r"D = [x_{min}, x_{max}] \times [y_{min}, y_{max}]")
    st.code(domain.notation(), language="text")

    st.markdown("**Tabla de limites del dominio**")
    st.dataframe(domain.as_table(), width="stretch", hide_index=True)

    lon_c, lat_c = domain.center
    metrics = pd.DataFrame(
        [
            ["Amplitud en longitud", f"{domain.width:.4f} grados"],
            ["Amplitud en latitud", f"{domain.height:.4f} grados"],
            ["Centro del dominio", f"lon {lon_c:.4f} / lat {lat_c:.4f}"],
            ["Area del rectangulo", f"{domain.area_deg2:.4f} grados cuadrados"],
            ["Area aproximada", f"{domain.area_km2:,.0f} km2"],
        ],
        columns=["Metrica derivada", "Valor"],
    )
    st.markdown("**Interpretacion del area representada**")
    st.dataframe(metrics, width="stretch", hide_index=True)
    note(
        "El dominio es el rectangulo minimo que contiene las localidades "
        "seleccionadas: xmin marca el limite occidental, xmax el oriental, ymin el "
        "sur y ymax el norte. Sobre este marco se construyen la cuadricula y la malla."
    )


# ---------------------------------------------------------------------------
# Actividades 4, 5 y 6
# ---------------------------------------------------------------------------
def _tab_visualizations(result: AnalysisResult) -> None:
    st.subheader("Actividades 4, 5 y 6. Puntos, cuadricula y malla")
    color_legend()
    chart_tabs = st.tabs(
        ["4. Puntos reales", "5. Cuadricula", "6. Malla visual", "Comparacion"]
    )

    with chart_tabs[0]:
        st.plotly_chart(
            charts.chart_points(result.clean, result.domain, result.country),
            width="stretch",
        )
        note(content.distribution_comment(result))

    with chart_tabs[1]:
        st.plotly_chart(charts.chart_grid(result.grid, result.country), width="stretch")
        st.dataframe(result.grid.as_table(), width="stretch", hide_index=True)

    with chart_tabs[2]:
        st.plotly_chart(
            charts.chart_mesh(result.clean, result.grid, result.country),
            width="stretch",
        )
        st.caption(
            f"Lineas horizontales: {result.grid.ny} | Lineas verticales: {result.grid.nx} | "
            f"Celdas: {result.grid.cells:,} | Puntos reales superpuestos: {len(result.clean):,}"
        )

    with chart_tabs[3]:
        st.markdown("**Puntos reales frente a puntos generados**")
        st.dataframe(
            real_vs_generated(result.clean, result.grid),
            width="stretch",
            hide_index=True,
        )


# ---------------------------------------------------------------------------
# Analisis complementario
# ---------------------------------------------------------------------------
def _tab_extra_analysis(result: AnalysisResult) -> None:
    st.subheader("Analisis complementario: densidad y resolucion")
    st.caption("Usa la malla como instrumento de medida, no solo como recurso visual.")

    st.plotly_chart(
        charts.chart_density(result.clean, result.grid, result.country),
        width="stretch",
    )

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Cobertura de la malla**")
        st.dataframe(result.occupancy.as_table(), width="stretch", hide_index=True)
    with right:
        st.markdown("**Celdas con mayor concentracion**")
        st.dataframe(
            result.occupancy.table.head(10), width="stretch", hide_index=True
        )

    st.markdown("**Sensibilidad a los valores de dx y dy**")
    st.dataframe(
        resolution_sensitivity(result.clean, result.domain),
        width="stretch",
        hide_index=True,
    )
    note(
        "Al reducir dx y dy crece el numero de nodos de forma cuadratica y baja el "
        "porcentaje de celdas ocupadas: mas detalle, mas celdas vacias y mas "
        "saturacion visual. Al aumentarlos ocurre lo contrario: menos celdas, mas "
        "legibilidad y mayor riesgo de ocultar diferencias internas."
    )

    vecinos = nearest_neighbor_km(result.clean)
    if vecinos.notna().any():
        tabla = (
            result.clean[[cfg.COL_CITY]]
            .assign(**{"Vecino mas cercano (km)": vecinos.round(1)})
            .sort_values("Vecino mas cercano (km)", ascending=False)
            .head(10)
        )
        st.markdown("**Localidades mas aisladas (mayor distancia al vecino mas cercano)**")
        st.dataframe(tabla, width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Actividad 7
# ---------------------------------------------------------------------------
def _tab_interpretation(result: AnalysisResult) -> None:
    st.subheader("Actividad 7. Interpretacion visual de resultados")
    columnas = st.columns(2)
    for i, (pregunta, respuesta) in enumerate(content.activity7_answers(result)):
        with columnas[i % 2]:
            answer_card(pregunta, respuesta)

    st.subheader("Preguntas de analisis del informe")
    for pregunta, respuesta in content.analysis_answers(result):
        with st.expander(pregunta, expanded=False):
            st.write(respuesta)

    st.subheader("Aplicaciones en Ingenieria de Sistemas")
    st.dataframe(
        pd.DataFrame(
            content.systems_applications(),
            columns=["Caso de aplicacion", "Como se usa el dominio y la malla"],
        ),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Conclusiones")
    for i, texto in enumerate(content.conclusions(result), start=1):
        st.markdown(f"**{i}.** {texto}")


# ---------------------------------------------------------------------------
# Informe
# ---------------------------------------------------------------------------
def _tab_report(result: AnalysisResult) -> None:
    st.subheader("Informe PDF: producto final de la practica")
    st.markdown(
        "El informe se genera en el momento con los datos y filtros actuales e "
        "incluye los 14 elementos exigidos en la seccion 'Producto final a entregar'."
    )
    st.dataframe(
        pd.DataFrame(content.report_index(), columns=["Seccion", "Contenido"]),
        width="stretch",
        hide_index=True,
    )

    if st.button("Generar informe PDF", type="primary", width="stretch"):
        with st.spinner("Construyendo el informe..."):
            st.session_state["pdf_bytes"] = build_report(result)
        st.success("Informe generado.")

    pdf_bytes = st.session_state.get("pdf_bytes")
    if pdf_bytes:
        st.download_button(
            "Descargar informe PDF",
            data=pdf_bytes,
            file_name=cfg.REPORT_FILENAME,
            mime="application/pdf",
            width="stretch",
        )
    st.caption(
        "Tambien se puede generar sin abrir la app ejecutando: python main.py "
        "(guarda el PDF en informe/ y las figuras en docs/figuras/)."
    )


# ---------------------------------------------------------------------------
# Codigo
# ---------------------------------------------------------------------------
def _tab_code(result: AnalysisResult) -> None:
    st.subheader("Codigo utilizado en Python")
    st.caption(
        "Version minima y autocontenida que reproduce las siete actividades. "
        "El proyecto completo es modular: paquete vizdominios/ + app.py + main.py."
    )
    st.code(content.code_annex(result), language="python")
    st.download_button(
        "Descargar codigo (.py)",
        data=content.code_annex(result).encode("utf-8"),
        file_name="practica02_codigo_minimo.py",
        mime="text/x-python",
        width="stretch",
    )


__all__ = ["TAB_LABELS", "render_tabs"]
