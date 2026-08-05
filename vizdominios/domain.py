"""Actividad 3: modelado del dominio geografico y de la cuadricula.

Contiene los objetos de dominio del proyecto:

- ``ColumnMap``: que columna del CSV representa ciudad, pais, latitud y longitud.
- ``GeoDomain``: el rectangulo D = [xmin, xmax] x [ymin, ymax].
- ``Grid``: la cuadricula regular generada dentro de ese dominio con dx y dy.

Todo el calculo espacial del proyecto pasa por estas tres clases, de modo que la
interfaz Streamlit, el script de consola y el informe PDF usan exactamente la
misma matematica.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from . import config as cfg


class ColumnDetectionError(ValueError):
    """No fue posible identificar las columnas minimas del dataset."""


# ---------------------------------------------------------------------------
# Deteccion de columnas
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ColumnMap:
    """Nombres reales de las columnas del CSV cargado."""

    city: str
    country: str
    latitude: str
    longitude: str
    region: str | None = None

    def as_table(self) -> pd.DataFrame:
        """Tabla lista para mostrar en la app y en el informe."""
        rows = [
            ["Ciudad o localidad", self.city, "Etiqueta del punto"],
            ["Pais", self.country, "Permite filtrar el pais de analisis"],
            ["Latitud", self.latitude, "Eje Y de la visualizacion (y)"],
            ["Longitud", self.longitude, "Eje X de la visualizacion (x)"],
        ]
        if self.region:
            rows.append(["Region", self.region, "Departamento o division administrativa"])
        return pd.DataFrame(rows, columns=["Rol", "Columna del CSV", "Uso en la practica"])


def find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    """Busca la primera columna que coincida con la lista de candidatos.

    Primero intenta coincidencia exacta (sin importar mayusculas) y luego
    coincidencia parcial, para tolerar nombres como ``gps_latitude_deg``.
    """
    columns = list(columns)
    lookup = {str(col).lower().strip(): col for col in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    for col in columns:
        normalized = str(col).lower().strip()
        if any(candidate in normalized for candidate in candidates):
            return col
    return None


def detect_columns(df: pd.DataFrame) -> ColumnMap:
    """Identifica las columnas de ciudad, pais, latitud y longitud.

    Raises:
        ColumnDetectionError: si falta alguna columna obligatoria.
    """
    columns = list(df.columns)
    city = find_column(columns, cfg.CITY_CANDIDATES)
    country = find_column(columns, cfg.COUNTRY_CANDIDATES)
    latitude = find_column(columns, cfg.LAT_CANDIDATES)
    longitude = find_column(columns, cfg.LON_CANDIDATES)
    region = find_column(columns, cfg.REGION_CANDIDATES)

    missing = [
        label
        for label, value in (
            ("ciudad/localidad", city),
            ("pais", country),
            ("latitud", latitude),
            ("longitud", longitude),
        )
        if value is None
    ]
    if missing:
        raise ColumnDetectionError(
            "No se detectaron columnas de " + ", ".join(missing) + ". "
            "Revisa el CSV o renombra las columnas."
        )
    return ColumnMap(
        city=str(city),
        country=str(country),
        latitude=str(latitude),
        longitude=str(longitude),
        region=str(region) if region else None,
    )


# ---------------------------------------------------------------------------
# Dominio geografico
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GeoDomain:
    """Dominio rectangular D = [xmin, xmax] x [ymin, ymax].

    x corresponde a la longitud y y a la latitud, tal como lo pide la practica.
    """

    xmin: float
    xmax: float
    ymin: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmin > self.xmax or self.ymin > self.ymax:
            raise ValueError(
                "Dominio invalido: se requiere xmin <= xmax y ymin <= ymax "
                f"(recibido x=[{self.xmin}, {self.xmax}] y=[{self.ymin}, {self.ymax}])."
            )

    # -- constructores -------------------------------------------------------
    @classmethod
    def from_dataframe(
        cls,
        data: pd.DataFrame,
        lon_col: str = cfg.COL_LON,
        lat_col: str = cfg.COL_LAT,
    ) -> "GeoDomain":
        """Calcula el dominio a partir de los minimos y maximos observados."""
        if data.empty:
            raise ValueError("No se puede calcular el dominio de una tabla vacia.")
        return cls(
            xmin=float(data[lon_col].min()),
            xmax=float(data[lon_col].max()),
            ymin=float(data[lat_col].min()),
            ymax=float(data[lat_col].max()),
        )

    # -- propiedades derivadas ----------------------------------------------
    @property
    def width(self) -> float:
        """Amplitud en grados de longitud (xmax - xmin)."""
        return self.xmax - self.xmin

    @property
    def height(self) -> float:
        """Amplitud en grados de latitud (ymax - ymin)."""
        return self.ymax - self.ymin

    @property
    def center(self) -> tuple[float, float]:
        """Centro geometrico del dominio como (longitud, latitud)."""
        return ((self.xmin + self.xmax) / 2, (self.ymin + self.ymax) / 2)

    @property
    def area_deg2(self) -> float:
        """Area del rectangulo en grados cuadrados."""
        return self.width * self.height

    @property
    def area_km2(self) -> float:
        """Area aproximada en km2 usando la latitud central como referencia."""
        lat_center = self.center[1]
        km_per_deg_lat = 110.574
        km_per_deg_lon = 111.320 * np.cos(np.radians(lat_center))
        return abs(self.height * km_per_deg_lat) * abs(self.width * km_per_deg_lon)

    def padded(self, margin: float = 0.8) -> "GeoDomain":
        """Dominio expandido, solo para dejar aire en los ejes de los graficos."""
        return GeoDomain(
            xmin=self.xmin - margin,
            xmax=self.xmax + margin,
            ymin=self.ymin - margin,
            ymax=self.ymax + margin,
        )

    def contains(self, lon: float, lat: float) -> bool:
        """Indica si un punto cae dentro del dominio (bordes incluidos)."""
        return self.xmin <= lon <= self.xmax and self.ymin <= lat <= self.ymax

    def rectangle(self) -> tuple[list[float], list[float]]:
        """Vertices cerrados del rectangulo como (lons, lats), utiles para dibujar."""
        lons = [self.xmin, self.xmax, self.xmax, self.xmin, self.xmin]
        lats = [self.ymin, self.ymin, self.ymax, self.ymax, self.ymin]
        return lons, lats

    # -- salidas para informe -----------------------------------------------
    def as_dict(self) -> dict[str, float]:
        return {
            "xmin": self.xmin,
            "xmax": self.xmax,
            "ymin": self.ymin,
            "ymax": self.ymax,
        }

    def as_table(self) -> pd.DataFrame:
        """Tabla exacta que solicita la Actividad 3 de la practica."""
        return pd.DataFrame(
            [
                ["Longitud minima (xmin)", self.xmin, "Limite occidental del dominio"],
                ["Longitud maxima (xmax)", self.xmax, "Limite oriental del dominio"],
                ["Latitud minima (ymin)", self.ymin, "Limite sur del dominio"],
                ["Latitud maxima (ymax)", self.ymax, "Limite norte del dominio"],
            ],
            columns=["Parametro", "Valor", "Interpretacion"],
        )

    def notation(self, decimals: int = 4) -> str:
        """Dominio en notacion matematica, por ejemplo D = [-81.27, -69.02] x ..."""
        return (
            f"D = [{self.xmin:.{decimals}f}, {self.xmax:.{decimals}f}] x "
            f"[{self.ymin:.{decimals}f}, {self.ymax:.{decimals}f}]"
        )


# ---------------------------------------------------------------------------
# Cuadricula regular
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Grid:
    """Cuadricula regular de puntos generada dentro de un ``GeoDomain``."""

    X: np.ndarray
    Y: np.ndarray
    dx: float
    dy: float
    domain: GeoDomain

    @classmethod
    def from_domain(cls, domain: GeoDomain, dx: float, dy: float) -> "Grid":
        """Genera la malla de coordenadas con ``numpy.meshgrid``.

        Se usa ``xmax + dx`` para que el borde derecho/superior del dominio
        quede cubierto, ya que ``np.arange`` excluye el limite superior.
        """
        if dx <= 0 or dy <= 0:
            raise ValueError("dx y dy deben ser mayores que cero.")
        x_grid = np.arange(domain.xmin, domain.xmax + dx, dx)
        y_grid = np.arange(domain.ymin, domain.ymax + dy, dy)
        X, Y = np.meshgrid(x_grid, y_grid)
        return cls(X=X, Y=Y, dx=float(dx), dy=float(dy), domain=domain)

    # -- dimensiones ---------------------------------------------------------
    @property
    def nx(self) -> int:
        """Cantidad de columnas (lineas verticales) de la cuadricula."""
        return int(self.X.shape[1])

    @property
    def ny(self) -> int:
        """Cantidad de filas (lineas horizontales) de la cuadricula."""
        return int(self.X.shape[0])

    @property
    def size(self) -> int:
        """Total de puntos generados: nx * ny."""
        return int(self.X.size)

    @property
    def cells(self) -> int:
        """Celdas rectangulares formadas por la malla: (nx - 1) * (ny - 1)."""
        return max(self.nx - 1, 0) * max(self.ny - 1, 0)

    @property
    def x_lines(self) -> np.ndarray:
        """Posiciones de las lineas verticales (longitudes)."""
        return self.X[0, :]

    @property
    def y_lines(self) -> np.ndarray:
        """Posiciones de las lineas horizontales (latitudes)."""
        return self.Y[:, 0]

    def as_dataframe(self) -> pd.DataFrame:
        """Puntos de la cuadricula en formato tabular (longitud, latitud)."""
        return pd.DataFrame(
            {
                cfg.COL_LON: self.X.ravel(),
                cfg.COL_LAT: self.Y.ravel(),
            }
        )

    def as_table(self) -> pd.DataFrame:
        """Resumen de parametros de la cuadricula para el informe."""
        return pd.DataFrame(
            [
                ["Separacion horizontal (dx)", f"{self.dx} grados"],
                ["Separacion vertical (dy)", f"{self.dy} grados"],
                ["Lineas verticales (nx)", f"{self.nx}"],
                ["Lineas horizontales (ny)", f"{self.ny}"],
                ["Puntos generados (nx * ny)", f"{self.size:,}"],
                ["Celdas de la malla", f"{self.cells:,}"],
            ],
            columns=["Parametro", "Valor"],
        )
