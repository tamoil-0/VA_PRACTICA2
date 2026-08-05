"""Tests del dominio geografico y de la cuadricula (Actividades 3, 5 y 6)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from vizdominios import config as cfg
from vizdominios.domain import (
    ColumnDetectionError,
    GeoDomain,
    Grid,
    detect_columns,
    find_column,
)


@pytest.fixture
def puntos() -> pd.DataFrame:
    """Cuatro localidades con coordenadas conocidas."""
    return pd.DataFrame(
        {
            cfg.COL_CITY: ["Puno", "Lima", "Iquitos", "Tacna"],
            cfg.COL_LON: [-70.0219, -77.0428, -73.2538, -70.2463],
            cfg.COL_LAT: [-15.8402, -12.0464, -3.7491, -18.0066],
        }
    )


# ---------------------------------------------------------------------------
# Deteccion de columnas
# ---------------------------------------------------------------------------
def test_find_column_acepta_coincidencia_exacta_y_parcial():
    assert find_column(["LATITUDE", "x"], ["latitude"]) == "LATITUDE"
    assert find_column(["gps_latitude_deg"], ["latitude"]) == "gps_latitude_deg"
    assert find_column(["nombre"], ["latitude"]) is None


def test_detect_columns_reconoce_esquema_de_kaggle():
    df = pd.DataFrame(
        columns=["city_name", "country_name", "region_name", "latitude", "longitude"]
    )
    columns = detect_columns(df)
    assert columns.city == "city_name"
    assert columns.latitude == "latitude"
    assert columns.longitude == "longitude"
    assert columns.region == "region_name"


def test_detect_columns_falla_si_faltan_coordenadas():
    df = pd.DataFrame(columns=["city_name", "country_name"])
    with pytest.raises(ColumnDetectionError):
        detect_columns(df)


# ---------------------------------------------------------------------------
# GeoDomain
# ---------------------------------------------------------------------------
def test_dominio_usa_minimos_y_maximos_observados(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    assert domain.xmin == pytest.approx(-77.0428)
    assert domain.xmax == pytest.approx(-70.0219)
    assert domain.ymin == pytest.approx(-18.0066)
    assert domain.ymax == pytest.approx(-3.7491)


def test_propiedades_derivadas_del_dominio(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    assert domain.width == pytest.approx(domain.xmax - domain.xmin)
    assert domain.height == pytest.approx(domain.ymax - domain.ymin)
    assert domain.area_deg2 == pytest.approx(domain.width * domain.height)
    assert domain.area_km2 > 0
    lon_c, lat_c = domain.center
    assert domain.contains(lon_c, lat_c)


def test_todos_los_puntos_caen_dentro_del_dominio(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    dentro = [
        domain.contains(lon, lat)
        for lon, lat in zip(puntos[cfg.COL_LON], puntos[cfg.COL_LAT])
    ]
    assert all(dentro)


def test_dominio_invalido_lanza_error():
    with pytest.raises(ValueError):
        GeoDomain(xmin=0, xmax=-1, ymin=0, ymax=1)


def test_dominio_vacio_lanza_error():
    with pytest.raises(ValueError):
        GeoDomain.from_dataframe(pd.DataFrame({cfg.COL_LON: [], cfg.COL_LAT: []}))


def test_rectangulo_del_dominio_es_cerrado(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    lons, lats = domain.rectangle()
    assert len(lons) == len(lats) == 5
    assert (lons[0], lats[0]) == (lons[-1], lats[-1])


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------
def test_cuadricula_cubre_todo_el_dominio(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    grid = Grid.from_domain(domain, 0.5, 0.5)
    # El primer nodo coincide con el minimo y el ultimo supera el maximo, de modo
    # que la cuadricula cubre el dominio completo sin dejar franjas fuera.
    assert grid.X.min() == pytest.approx(domain.xmin)
    assert grid.Y.min() == pytest.approx(domain.ymin)
    assert grid.X.max() >= domain.xmax
    assert grid.Y.max() >= domain.ymax


def test_separacion_entre_nodos_es_constante(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    grid = Grid.from_domain(domain, 0.5, 0.25)
    assert np.allclose(np.diff(grid.x_lines), 0.5)
    assert np.allclose(np.diff(grid.y_lines), 0.25)


def test_dimensiones_y_celdas_de_la_malla(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    grid = Grid.from_domain(domain, 1.0, 1.0)
    assert grid.size == grid.nx * grid.ny
    assert grid.cells == (grid.nx - 1) * (grid.ny - 1)
    assert len(grid.as_dataframe()) == grid.size


def test_reducir_el_paso_aumenta_los_nodos(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    grueso = Grid.from_domain(domain, 1.0, 1.0)
    fino = Grid.from_domain(domain, 0.25, 0.25)
    assert fino.size > grueso.size


def test_paso_invalido_lanza_error(puntos):
    domain = GeoDomain.from_dataframe(puntos)
    with pytest.raises(ValueError):
        Grid.from_domain(domain, 0, 0.5)
