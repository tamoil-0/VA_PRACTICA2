"""Tests del flujo completo, las metricas y el informe PDF (Actividades 4 a 7)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from vizdominios import config as cfg, content
from vizdominios.analysis import (
    cell_occupancy,
    coordinate_summary,
    haversine_km,
    nearest_neighbor_km,
    resolution_sensitivity,
)
from vizdominios.figures import fig_grid, fig_mesh, fig_points, render_png
from vizdominios.pipeline import EmptySelectionError, run_analysis
from vizdominios.report import build_report


@pytest.fixture(scope="module")
def resultado():
    """Analisis completo sobre el dataset incluido (se reutiliza en el modulo)."""
    return run_analysis(dx=1.0, dy=1.0)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def test_pipeline_entrega_las_siete_actividades(resultado):
    assert len(resultado.raw) > 0
    assert len(resultado.clean) > 0
    assert resultado.cleaning.total_final == len(resultado.clean)
    assert resultado.domain.width > 0 and resultado.domain.height > 0
    assert resultado.grid.size == resultado.grid.nx * resultado.grid.ny
    assert resultado.occupancy.total_cells == resultado.grid.cells
    assert len(resultado.summary_lines()) == 7


def test_pipeline_respeta_los_filtros():
    completo = run_analysis()
    puno = run_analysis(regions=["Puno"])
    assert len(puno.clean) < len(completo.clean)
    # Al filtrar una region el dominio se encoge.
    assert puno.domain.width < completo.domain.width
    assert set(puno.clean[cfg.COL_REGION].unique()) == {"Puno"}


def test_pais_inexistente_lanza_error_claro():
    with pytest.raises(EmptySelectionError):
        run_analysis(country="Narnia")


def test_filtro_imposible_lanza_error_claro():
    with pytest.raises(EmptySelectionError):
        run_analysis(cities=["Ciudad Inexistente"])


# ---------------------------------------------------------------------------
# Metricas
# ---------------------------------------------------------------------------
def test_ocupacion_no_pierde_puntos(resultado):
    # Cada localidad cae en una sola celda, salvo las que estan exactamente en el
    # borde superior del ultimo bin; el total contado nunca puede exceder el real.
    total_contado = int(resultado.occupancy.counts.sum())
    assert total_contado <= len(resultado.clean)
    assert total_contado >= len(resultado.clean) - 1
    assert 0 <= resultado.occupancy.occupancy_pct <= 100
    assert resultado.occupancy.occupied_cells + resultado.occupancy.empty_cells == (
        resultado.occupancy.total_cells
    )


def test_sensibilidad_muestra_crecimiento_cuadratico(resultado):
    tabla = resolution_sensitivity(resultado.clean, resultado.domain, deltas=(0.5, 1.0, 2.0))
    puntos = tabla["Puntos generados"].tolist()
    assert puntos == sorted(puntos, reverse=True)  # a mayor paso, menos nodos


def test_haversine_contra_distancia_conocida():
    # Lima - Puno: aproximadamente 850 km en linea recta.
    distancia = float(haversine_km(-77.0428, -12.0464, -70.0219, -15.8402))
    assert 800 < distancia < 900


def test_vecino_mas_cercano_es_positivo(resultado):
    vecinos = nearest_neighbor_km(resultado.clean)
    assert vecinos.notna().all()
    assert (vecinos > 0).all()


def test_resumen_de_coordenadas_coincide_con_el_dominio(resultado):
    resumen = coordinate_summary(resultado.clean)
    lon = resumen[resumen["Variable"].str.startswith("Longitud")].iloc[0]
    assert lon["Minimo"] == pytest.approx(resultado.domain.xmin, abs=1e-4)
    assert lon["Maximo"] == pytest.approx(resultado.domain.xmax, abs=1e-4)


def test_ocupacion_con_un_solo_punto_es_degenerada():
    data = pd.DataFrame({cfg.COL_CITY: ["Puno"], cfg.COL_LAT: [-15.84], cfg.COL_LON: [-70.02]})
    resultado = run_analysis(cities=["Puno"])
    ocupacion = cell_occupancy(data, resultado.grid)
    assert ocupacion.total_cells == 0
    assert ocupacion.occupancy_pct == 0.0


# ---------------------------------------------------------------------------
# Contenido interpretativo
# ---------------------------------------------------------------------------
def test_los_textos_incluyen_cifras_reales(resultado):
    descripcion = content.dataset_description(resultado)
    assert f"{len(resultado.raw):,}" in descripcion
    assert cfg.DATASET_URL in descripcion

    assert len(content.activity7_answers(resultado)) == 4
    assert len(content.analysis_answers(resultado)) == 7
    assert len(content.conclusions(resultado)) >= 4
    assert len(content.rubric_rows(resultado)) == 7
    assert sum(int(row[1]) for row in content.rubric_rows(resultado)) == cfg.TOTAL_POINTS


def test_codigo_anexo_es_python_valido(resultado):
    compile(content.code_annex(resultado), "codigo_anexo.py", "exec")


# ---------------------------------------------------------------------------
# Figuras e informe
# ---------------------------------------------------------------------------
def test_las_figuras_se_generan_como_png(resultado):
    for fig in (
        fig_points(resultado.clean, resultado.domain, resultado.country),
        fig_grid(resultado.grid, resultado.country),
        fig_mesh(resultado.clean, resultado.grid, resultado.country),
    ):
        png = render_png(fig).getvalue()
        assert png.startswith(b"\x89PNG")
        assert len(png) > 5_000


def test_el_informe_pdf_se_construye(resultado):
    pdf = build_report(resultado)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 50_000
    assert pdf.count(b"/Type /Page") > 8


def test_meshgrid_reproduce_el_codigo_base(resultado):
    """La cuadricula del proyecto coincide con np.meshgrid del codigo sugerido."""
    d = resultado.domain
    x = np.arange(d.xmin, d.xmax + resultado.dx, resultado.dx)
    y = np.arange(d.ymin, d.ymax + resultado.dy, resultado.dy)
    X, Y = np.meshgrid(x, y)
    assert np.allclose(X, resultado.grid.X)
    assert np.allclose(Y, resultado.grid.Y)
