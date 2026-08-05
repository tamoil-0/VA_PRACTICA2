"""Actividad 7: metricas que respaldan la interpretacion visual con numeros.

Las preguntas de analisis de la practica ("que ocurre si se reduce dx y dy",
"que diferencia hay entre puntos reales y generados") se pueden responder de
forma cualitativa, pero aqui se responden con evidencia cuantitativa:

- ``coordinate_summary``: estadisticos descriptivos de latitud y longitud.
- ``cell_occupancy``: cuantos puntos reales cae en cada celda de la malla.
- ``resolution_sensitivity``: efecto real de cambiar dx y dy.
- ``nearest_neighbor_km``: separacion tipica entre localidades en kilometros.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config as cfg
from .domain import GeoDomain, Grid


# ---------------------------------------------------------------------------
# Estadisticos de coordenadas
# ---------------------------------------------------------------------------
def coordinate_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Resumen descriptivo de longitud y latitud de los puntos reales."""
    rows = []
    for label, col in (("Longitud (x)", cfg.COL_LON), ("Latitud (y)", cfg.COL_LAT)):
        serie = data[col].astype(float)
        rows.append(
            [
                label,
                round(float(serie.min()), 4),
                round(float(serie.max()), 4),
                round(float(serie.mean()), 4),
                round(float(serie.std(ddof=1)) if len(serie) > 1 else 0.0, 4),
                round(float(serie.max() - serie.min()), 4),
            ]
        )
    return pd.DataFrame(
        rows, columns=["Variable", "Minimo", "Maximo", "Media", "Desv. estandar", "Rango"]
    )


def haversine_km(lon1: np.ndarray, lat1: np.ndarray, lon2: np.ndarray, lat2: np.ndarray) -> np.ndarray:
    """Distancia haversine en kilometros entre pares de coordenadas."""
    lon1, lat1, lon2, lat2 = map(np.radians, (lon1, lat1, lon2, lat2))
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * cfg.EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def nearest_neighbor_km(data: pd.DataFrame) -> pd.Series:
    """Distancia al vecino mas cercano, en km, para cada punto real."""
    lon = data[cfg.COL_LON].to_numpy(dtype=float)
    lat = data[cfg.COL_LAT].to_numpy(dtype=float)
    n = len(lon)
    if n < 2:
        return pd.Series([np.nan] * n, index=data.index, name="Vecino mas cercano (km)")
    dist = haversine_km(lon[:, None], lat[:, None], lon[None, :], lat[None, :])
    np.fill_diagonal(dist, np.inf)
    return pd.Series(dist.min(axis=1), index=data.index, name="Vecino mas cercano (km)")


# ---------------------------------------------------------------------------
# Ocupacion de la malla
# ---------------------------------------------------------------------------
@dataclass
class OccupancyResult:
    """Resultado del conteo de puntos reales por celda de la malla."""

    counts: np.ndarray          # matriz (ny-1, nx-1) con el conteo por celda
    total_cells: int
    occupied_cells: int
    max_count: int
    table: pd.DataFrame         # celdas con al menos un punto, ordenadas

    @property
    def empty_cells(self) -> int:
        return self.total_cells - self.occupied_cells

    @property
    def occupancy_pct(self) -> float:
        if self.total_cells == 0:
            return 0.0
        return 100.0 * self.occupied_cells / self.total_cells

    def as_table(self) -> pd.DataFrame:
        """Metricas de cobertura listas para el informe."""
        return pd.DataFrame(
            [
                ["Celdas totales de la malla", f"{self.total_cells:,}"],
                ["Celdas con al menos un punto real", f"{self.occupied_cells:,}"],
                ["Celdas vacias", f"{self.empty_cells:,}"],
                ["Cobertura de la malla", f"{self.occupancy_pct:.1f} %"],
                ["Maxima concentracion en una celda", f"{self.max_count} puntos"],
            ],
            columns=["Metrica de cobertura", "Valor"],
        )


def cell_occupancy(data: pd.DataFrame, grid: Grid) -> OccupancyResult:
    """Cuenta cuantos puntos reales caen dentro de cada celda de la malla.

    Es la metrica que convierte la malla en una herramienta analitica: permite
    detectar zonas densas y zonas sin cobertura dentro del mismo dominio.
    """
    x_edges = grid.x_lines
    y_edges = grid.y_lines
    if len(x_edges) < 2 or len(y_edges) < 2:
        empty = np.zeros((0, 0), dtype=int)
        return OccupancyResult(empty, 0, 0, 0, pd.DataFrame())

    counts, _, _ = np.histogram2d(
        data[cfg.COL_LON].to_numpy(dtype=float),
        data[cfg.COL_LAT].to_numpy(dtype=float),
        bins=[x_edges, y_edges],
    )
    counts = counts.T.astype(int)  # filas = latitud, columnas = longitud

    rows = []
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            if counts[i, j] > 0:
                rows.append(
                    [
                        f"F{i + 1}-C{j + 1}",
                        f"[{x_edges[j]:.2f}, {x_edges[j + 1]:.2f}]",
                        f"[{y_edges[i]:.2f}, {y_edges[i + 1]:.2f}]",
                        int(counts[i, j]),
                    ]
                )
    table = pd.DataFrame(
        rows, columns=["Celda", "Rango de longitud", "Rango de latitud", "Puntos reales"]
    ).sort_values("Puntos reales", ascending=False).reset_index(drop=True)

    return OccupancyResult(
        counts=counts,
        total_cells=int(counts.size),
        occupied_cells=int((counts > 0).sum()),
        max_count=int(counts.max()) if counts.size else 0,
        table=table,
    )


# ---------------------------------------------------------------------------
# Sensibilidad a dx y dy (preguntas 5 y 6 del informe)
# ---------------------------------------------------------------------------
def resolution_sensitivity(
    data: pd.DataFrame,
    domain: GeoDomain,
    deltas: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0),
) -> pd.DataFrame:
    """Compara la cuadricula para distintos valores de dx = dy.

    Demuestra numericamente el efecto de la resolucion: al reducir el paso
    crecen los puntos generados y baja el porcentaje de celdas ocupadas
    (mas detalle, mas celdas vacias); al aumentarlo ocurre lo contrario.
    """
    rows = []
    for delta in deltas:
        grid = Grid.from_domain(domain, delta, delta)
        occupancy = cell_occupancy(data, grid)
        rows.append(
            [
                f"{delta}",
                grid.nx,
                grid.ny,
                grid.size,
                grid.cells,
                occupancy.occupied_cells,
                f"{occupancy.occupancy_pct:.1f} %",
                occupancy.max_count,
            ]
        )
    return pd.DataFrame(
        rows,
        columns=[
            "dx = dy",
            "Lineas verticales",
            "Lineas horizontales",
            "Puntos generados",
            "Celdas",
            "Celdas ocupadas",
            "Cobertura",
            "Max. puntos por celda",
        ],
    )


# ---------------------------------------------------------------------------
# Comparacion puntos reales vs generados (pregunta b de la Actividad 7)
# ---------------------------------------------------------------------------
def real_vs_generated(data: pd.DataFrame, grid: Grid) -> pd.DataFrame:
    """Tabla comparativa entre los puntos observados y los puntos sinteticos."""
    nn = nearest_neighbor_km(data)
    paso_km = grid.dx * 111.32 * float(np.cos(np.radians(grid.domain.center[1])))
    return pd.DataFrame(
        [
            ["Origen", "Dataset real (Kaggle / muestra Peru)", "Generados con numpy.meshgrid"],
            ["Cantidad", f"{len(data):,} localidades", f"{grid.size:,} nodos"],
            ["Distribucion", "Irregular, depende del poblamiento", "Regular, paso constante"],
            [
                "Separacion tipica",
                f"{nn.mean():.1f} km promedio al vecino mas cercano" if nn.notna().any() else "n/d",
                f"{paso_km:.1f} km aprox. entre nodos (dx = {grid.dx})",
            ],
            ["Significado", "Un lugar que existe en el territorio", "Una posicion de referencia del espacio"],
            ["Uso analitico", "Mostrar donde estan los hechos", "Medir, comparar y agregar por celdas"],
        ],
        columns=["Criterio", "Puntos reales", "Puntos de la cuadricula"],
    )


def key_metrics(
    raw: pd.DataFrame,
    clean: pd.DataFrame,
    domain: GeoDomain,
    grid: Grid,
) -> dict[str, str]:
    """Metricas principales que se muestran como tarjetas en la app."""
    return {
        "Registros del archivo": f"{len(raw):,}",
        "Localidades limpias": f"{len(clean):,}",
        "Amplitud del dominio": f"{domain.width:.2f} x {domain.height:.2f} grados",
        "Area aproximada": f"{domain.area_km2:,.0f} km2",
        "Puntos de cuadricula": f"{grid.size:,}",
        "Celdas de la malla": f"{grid.cells:,}",
    }
