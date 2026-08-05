"""Tests de carga, limpieza y filtrado (Actividades 1 y 2)."""

from __future__ import annotations

import pandas as pd
import pytest

from vizdominios import config as cfg
from vizdominios.dataio import (
    add_geo_groups,
    clean_data,
    column_profile,
    dataset_overview,
    filter_geo_data,
    load_dataset,
    to_geojson,
)
from vizdominios.domain import detect_columns


@pytest.fixture
def crudo() -> pd.DataFrame:
    """Dataset sucio a proposito: nulos, texto, duplicados, otro pais y rango invalido."""
    return pd.DataFrame(
        {
            "city_name": ["Puno", "Lima", "Sucre", "Vacio", "Texto", "Puno", "Imposible"],
            "country_name": ["Peru", "Peru", "Bolivia", "Peru", "Peru", "Peru", "Peru"],
            "region_name": ["Puno", "Lima", "Chuquisaca", "Puno", "Lima", "Puno", "Puno"],
            "latitude": [-15.8402, -12.0464, -19.03, None, "abc", -15.8402, 95.0],
            "longitude": [-70.0219, -77.0428, -65.26, -70.0, -77.0, -70.0219, -70.0],
        }
    )


def test_dataset_incluido_se_carga_y_tiene_columnas_minimas():
    df = load_dataset(cfg.DEFAULT_DATASET)
    columns = detect_columns(df)
    assert len(df) > 0
    assert {columns.city, columns.country, columns.latitude, columns.longitude} <= set(df.columns)


def test_limpieza_descarta_cada_tipo_de_registro_invalido(crudo):
    columns = detect_columns(crudo)
    clean, report = clean_data(crudo, columns, "Peru")

    assert report.total_inicial == 7
    assert report.sin_pais == 1                    # Bolivia
    assert report.coordenadas_no_numericas == 2    # None y "abc"
    assert report.coordenadas_fuera_de_rango == 1  # latitud 95
    assert report.duplicados == 1                  # Puno repetido
    assert report.total_final == len(clean) == 2
    assert sorted(clean[cfg.COL_CITY]) == ["Lima", "Puno"]


def test_limpieza_renombra_a_columnas_canonicas(crudo):
    columns = detect_columns(crudo)
    clean, _ = clean_data(crudo, columns, "Peru")
    for col in cfg.CLEAN_COLUMNS:
        assert col in clean.columns
    assert pd.api.types.is_numeric_dtype(clean[cfg.COL_LAT])
    assert pd.api.types.is_numeric_dtype(clean[cfg.COL_LON])


def test_auditoria_de_limpieza_es_consistente(crudo):
    columns = detect_columns(crudo)
    _, report = clean_data(crudo, columns, "Peru")
    descartados = (
        report.sin_pais
        + report.coordenadas_no_numericas
        + report.coordenadas_fuera_de_rango
        + report.duplicados
    )
    assert report.total_inicial - descartados == report.total_final


def test_grupos_geograficos_clasifican_regiones_conocidas():
    data = pd.DataFrame(
        {
            cfg.COL_CITY: ["Puno", "Lima", "Iquitos", "Piura"],
            cfg.COL_REGION: ["Puno", "Lima", "Loreto", "Piura"],
            cfg.COL_LAT: [-15.84, -12.05, -3.75, -5.19],
            cfg.COL_LON: [-70.02, -77.04, -73.25, -80.63],
        }
    )
    grouped = add_geo_groups(data)
    esperado_macro = {"Puno": "Sur", "Lima": "Centro", "Iquitos": "Norte", "Piura": "Norte"}
    esperado_natural = {"Puno": "Sierra", "Lima": "Costa", "Iquitos": "Selva", "Piura": "Costa"}
    for _, row in grouped.iterrows():
        ciudad = row[cfg.COL_CITY]
        assert row[cfg.COL_MACRO] == esperado_macro[ciudad]
        assert row[cfg.COL_NATURAL] == esperado_natural[ciudad]


def test_filtros_vacios_no_alteran_la_tabla():
    df = add_geo_groups(
        pd.DataFrame(
            {
                cfg.COL_CITY: ["Puno", "Lima"],
                cfg.COL_REGION: ["Puno", "Lima"],
                cfg.COL_LAT: [-15.84, -12.05],
                cfg.COL_LON: [-70.02, -77.04],
            }
        )
    )
    assert len(filter_geo_data(df)) == 2
    assert len(filter_geo_data(df, regions=["Puno"])) == 1
    assert len(filter_geo_data(df, natural_regions=["Costa"])) == 1
    assert len(filter_geo_data(df, cities=["Lima", "Puno"])) == 2


def test_exploracion_responde_las_cuatro_preguntas(crudo):
    columns = detect_columns(crudo)
    overview = dataset_overview(crudo, columns)
    assert len(overview) == 6
    assert column_profile(crudo).shape[0] == len(crudo.columns)


def test_geojson_respeta_el_orden_lon_lat():
    data = pd.DataFrame(
        {cfg.COL_CITY: ["Puno"], cfg.COL_LAT: [-15.8402], cfg.COL_LON: [-70.0219]}
    )
    geojson = to_geojson(data)
    coords = geojson["features"][0]["geometry"]["coordinates"]
    assert coords == [-70.0219, -15.8402]
    assert geojson["features"][0]["properties"][cfg.COL_CITY] == "Puno"
