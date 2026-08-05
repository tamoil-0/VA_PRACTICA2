"""Punto de entrada de la aplicacion Streamlit.

Practica Calificada 02 - Unidad 2 - Visualizacion de Datos
Visualizacion de dominios geograficos mediante puntos, cuadriculas y mallas.

Ejecutar con:
    python -m streamlit run app.py

Este archivo solo conecta piezas: la barra lateral entrega la seleccion del
usuario, ``run_analysis`` ejecuta las siete actividades y ``render_tabs`` las
presenta. Toda la logica vive en el paquete ``vizdominios``.
"""

from __future__ import annotations

import streamlit as st

from vizdominios.pipeline import EmptySelectionError, run_analysis
from vizdominios.ui.sidebar import render_filters, render_sidebar
from vizdominios.ui.tabs import render_tabs
from vizdominios.ui.theme import inject_css, page_header, setup_page


def main() -> None:
    setup_page()
    inject_css()
    page_header()

    selection = render_sidebar()

    try:
        # Primera pasada: tabla limpia del pais completo, necesaria para poblar
        # las opciones de los filtros geograficos con valores reales.
        base_result = run_analysis(
            dataframe=selection.dataframe,
            country=selection.country,
            dx=selection.dx,
            dy=selection.dy,
        )
    except EmptySelectionError as exc:
        st.error(str(exc))
        st.stop()

    selection = render_filters(selection, base_result.base)
    has_filters = any(
        [selection.regions, selection.macro_zones, selection.natural_regions, selection.cities]
    )

    if has_filters:
        try:
            result = run_analysis(
                dataframe=selection.dataframe,
                country=selection.country,
                dx=selection.dx,
                dy=selection.dy,
                regions=selection.regions,
                macro_zones=selection.macro_zones,
                natural_regions=selection.natural_regions,
                cities=selection.cities,
            )
        except EmptySelectionError as exc:
            st.error(str(exc))
            st.stop()
    else:
        result = base_result

    result.source_label = selection.source_label
    render_tabs(result)


if __name__ == "__main__":
    main()
