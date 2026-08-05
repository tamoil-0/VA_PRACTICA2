"""Barra lateral: fuente de datos, pais, parametros dx/dy y filtros geograficos."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

from .. import config as cfg
from ..dataio import available_countries, load_dataset
from ..domain import ColumnDetectionError, detect_columns


@dataclass
class Selection:
    """Todo lo que el usuario eligio en la barra lateral."""

    dataframe: pd.DataFrame
    source_label: str
    country: str
    dx: float
    dy: float
    regions: list[str] = field(default_factory=list)
    macro_zones: list[str] = field(default_factory=list)
    natural_regions: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)


@st.cache_data(show_spinner=False)
def _load_default() -> pd.DataFrame:
    """Dataset incluido en el repositorio (cacheado entre recargas)."""
    return load_dataset(cfg.DEFAULT_DATASET)


def render_sidebar() -> Selection:
    """Dibuja los controles y devuelve la seleccion del usuario.

    Los filtros geograficos se construyen a partir del propio dataset, por lo
    que la app funciona igual con la muestra incluida o con el CSV completo
    descargado de Kaggle.
    """
    with st.sidebar:
        st.header("Configuracion del analisis")

        uploaded = st.file_uploader(
            "CSV de Kaggle (opcional)",
            type=["csv"],
            help="Si no subes nada se usa el dataset incluido en data/.",
        )
        if uploaded is not None:
            dataframe = load_dataset(uploaded)
            source_label = uploaded.name
        else:
            dataframe = _load_default()
            source_label = cfg.DEFAULT_DATASET.name
        st.caption(f"Archivo en uso: **{source_label}** ({len(dataframe):,} registros)")

        try:
            columns = detect_columns(dataframe)
        except ColumnDetectionError as exc:
            st.error(str(exc))
            st.stop()

        countries = available_countries(dataframe, columns)
        default_index = countries.index(cfg.DEFAULT_COUNTRY) if cfg.DEFAULT_COUNTRY in countries else 0
        country = st.selectbox("Pais de analisis (Actividad 2)", countries, index=default_index)

        st.divider()
        st.subheader("Cuadricula (Actividad 5)")
        dx = st.slider("Separacion horizontal dx", 0.1, 3.0, cfg.DEFAULT_DX, 0.05)
        dy = st.slider("Separacion vertical dy", 0.1, 3.0, cfg.DEFAULT_DY, 0.05)
        st.caption(
            "dx y dy estan en grados. Valores pequenos dan mas detalle; "
            "valores grandes simplifican la lectura."
        )

        # Los filtros necesitan la tabla ya limpia: se construyen mas abajo, en
        # render_filters(), una vez que el pipeline entrego la tabla base.
        selection = Selection(
            dataframe=dataframe,
            source_label=source_label,
            country=country,
            dx=dx,
            dy=dy,
        )
    return selection


def render_filters(selection: Selection, base: pd.DataFrame) -> Selection:
    """Anade los filtros geograficos usando los valores presentes en los datos."""
    with st.sidebar:
        st.divider()
        st.subheader("Filtros geograficos")
        st.caption(
            "Recalculan la tabla limpia, el dominio, la cuadricula, la malla, "
            "las metricas y el informe PDF."
        )

        if cfg.COL_REGION in base.columns:
            options = sorted(base[cfg.COL_REGION].dropna().astype(str).unique())
            selection.regions = st.multiselect(
                "Region / departamento", options, placeholder="Todas las regiones"
            )
        macro_options = sorted(base[cfg.COL_MACRO].dropna().astype(str).unique())
        selection.macro_zones = st.multiselect(
            "Zona macro", macro_options, placeholder="Norte, Centro o Sur"
        )
        natural_options = sorted(base[cfg.COL_NATURAL].dropna().astype(str).unique())
        selection.natural_regions = st.multiselect(
            "Region natural", natural_options, placeholder="Costa, Sierra o Selva"
        )
        city_options = sorted(base[cfg.COL_CITY].dropna().astype(str).unique())
        selection.cities = st.multiselect(
            "Ciudad o localidad", city_options, placeholder="Todas las localidades"
        )

        st.divider()
        st.caption(f"Dataset original: {cfg.DATASET_URL}")
        st.caption(f"Repositorio: {cfg.REPO_URL}")
    return selection
