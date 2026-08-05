"""Orquestador del flujo completo de la practica.

``run_analysis`` ejecuta en un solo paso las siete actividades de la practica y
devuelve un ``AnalysisResult`` con todos los productos intermedios. La app
Streamlit, el script de consola ``main.py``, los tests y el generador de PDF
consumen este mismo objeto, por lo que los tres caminos producen siempre
resultados identicos.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from . import config as cfg
from .analysis import OccupancyResult, cell_occupancy
from .dataio import (
    CleaningReport,
    add_geo_groups,
    clean_data,
    filter_geo_data,
    load_dataset,
)
from .domain import ColumnMap, GeoDomain, Grid, detect_columns


@dataclass
class AnalysisResult:
    """Productos de las siete actividades, listos para mostrar o exportar."""

    raw: pd.DataFrame            # Actividad 1: dataset original
    columns: ColumnMap           # Actividad 1: columnas detectadas
    base: pd.DataFrame           # Actividad 2: tabla limpia del pais completo
    clean: pd.DataFrame          # Actividad 2 + filtros interactivos aplicados
    cleaning: CleaningReport     # Actividad 2: auditoria de limpieza
    domain: GeoDomain            # Actividad 3: dominio rectangular D
    grid: Grid                   # Actividad 5: cuadricula regular
    occupancy: OccupancyResult   # Actividad 6/7: puntos reales por celda
    country: str
    source_label: str

    @property
    def dx(self) -> float:
        return self.grid.dx

    @property
    def dy(self) -> float:
        return self.grid.dy

    def summary_lines(self) -> list[str]:
        """Resumen de una linea por actividad, util para la consola."""
        return [
            f"Actividad 1  Archivo: {self.source_label} | {len(self.raw):,} registros | {len(self.raw.columns)} columnas",
            f"Actividad 2  Tabla limpia de {self.country}: {len(self.clean):,} localidades",
            f"Actividad 3  {self.domain.notation()}",
            f"Actividad 4  Puntos reales graficados: {len(self.clean):,}",
            f"Actividad 5  Cuadricula dx={self.dx} dy={self.dy}: {self.grid.nx} x {self.grid.ny} = {self.grid.size:,} puntos",
            f"Actividad 6  Malla: {self.grid.ny} lineas horizontales y {self.grid.nx} lineas verticales ({self.grid.cells:,} celdas)",
            f"Actividad 7  Cobertura de la malla: {self.occupancy.occupied_cells:,} de {self.occupancy.total_cells:,} celdas ocupadas ({self.occupancy.occupancy_pct:.1f} %)",
        ]


class EmptySelectionError(ValueError):
    """La combinacion de pais y filtros no deja ningun registro utilizable."""


def run_analysis(
    source: Any = None,
    country: str = cfg.DEFAULT_COUNTRY,
    dx: float = cfg.DEFAULT_DX,
    dy: float = cfg.DEFAULT_DY,
    regions: list[str] | None = None,
    macro_zones: list[str] | None = None,
    natural_regions: list[str] | None = None,
    cities: list[str] | None = None,
    dataframe: pd.DataFrame | None = None,
) -> AnalysisResult:
    """Ejecuta el flujo completo: carga -> limpieza -> dominio -> cuadricula.

    Args:
        source: ruta o buffer del CSV. ``None`` usa el dataset incluido.
        country: pais a analizar (Actividad 2).
        dx, dy: separacion horizontal y vertical de la cuadricula (Actividad 5).
        regions, macro_zones, natural_regions, cities: filtros opcionales.
        dataframe: DataFrame ya cargado; evita releer el archivo desde la app.

    Raises:
        EmptySelectionError: si tras limpiar o filtrar no queda ningun registro.
    """
    raw = dataframe if dataframe is not None else load_dataset(source)
    columns = detect_columns(raw)
    clean, cleaning = clean_data(raw, columns, country)
    if clean.empty:
        raise EmptySelectionError(
            f"No quedaron registros validos para '{country}'. "
            "Revisa el CSV cargado o elige otro pais."
        )

    base = add_geo_groups(clean)
    filtered = filter_geo_data(base, regions, macro_zones, natural_regions, cities)
    if filtered.empty:
        raise EmptySelectionError(
            "Los filtros seleccionados no devuelven localidades. Quita algun filtro."
        )

    domain = GeoDomain.from_dataframe(filtered)
    grid = Grid.from_domain(domain, dx, dy)
    occupancy = cell_occupancy(filtered, grid)

    if isinstance(source, (str, Path)):
        source_label = Path(source).name
    elif source is None and dataframe is None:
        source_label = cfg.DEFAULT_DATASET.name
    else:
        source_label = getattr(source, "name", "CSV cargado por el usuario")

    return AnalysisResult(
        raw=raw,
        columns=columns,
        base=base,
        clean=filtered,
        cleaning=cleaning,
        domain=domain,
        grid=grid,
        occupancy=occupancy,
        country=country,
        source_label=str(source_label),
    )
