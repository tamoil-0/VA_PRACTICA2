"""Actividades 1 y 2: carga, exploracion, limpieza y filtrado del dataset.

El flujo es siempre el mismo:

``load_dataset`` -> ``detect_columns`` -> ``clean_data`` -> ``add_geo_groups``
-> ``filter_geo_data``

Cada paso devuelve un ``DataFrame`` nuevo (no muta el anterior) y ``clean_data``
entrega un reporte de limpieza con el conteo de registros descartados en cada
etapa, que es la evidencia que pide la Actividad 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from . import config as cfg
from .domain import ColumnMap

# ---------------------------------------------------------------------------
# Agrupaciones geograficas del Peru (usadas para los filtros de la app)
# ---------------------------------------------------------------------------
NORTH_REGIONS = {
    "tumbes", "piura", "lambayeque", "la libertad", "cajamarca",
    "amazonas", "san martin", "loreto",
}
CENTER_REGIONS = {
    "lima", "callao", "ancash", "huanuco", "pasco", "junin",
    "ucayali", "huancavelica",
}
SOUTH_REGIONS = {
    "ica", "ayacucho", "apurimac", "cusco", "arequipa", "puno",
    "moquegua", "tacna", "madre de dios",
}
COAST_REGIONS = {
    "tumbes", "piura", "lambayeque", "la libertad", "ancash", "lima",
    "callao", "ica", "arequipa", "moquegua", "tacna",
}
HIGHLAND_REGIONS = {
    "cajamarca", "ancash", "huanuco", "pasco", "junin", "huancavelica",
    "ayacucho", "apurimac", "cusco", "puno", "arequipa",
}
JUNGLE_REGIONS = {"amazonas", "san martin", "loreto", "ucayali", "madre de dios"}


@dataclass
class CleaningReport:
    """Trazabilidad de la limpieza (Actividad 2)."""

    total_inicial: int = 0
    sin_pais: int = 0
    coordenadas_no_numericas: int = 0
    coordenadas_fuera_de_rango: int = 0
    duplicados: int = 0
    total_final: int = 0
    pais: str = ""
    pasos: list[tuple[str, int]] = field(default_factory=list)

    def as_table(self) -> pd.DataFrame:
        """Tabla de auditoria: cuantos registros quedan tras cada paso."""
        rows = [
            ["Registros del archivo original", self.total_inicial],
            [f"Descartados por no pertenecer a {self.pais}", -self.sin_pais],
            ["Descartados por latitud/longitud no numerica o vacia", -self.coordenadas_no_numericas],
            ["Descartados por coordenadas fuera de rango valido", -self.coordenadas_fuera_de_rango],
            ["Descartados por ser duplicados exactos", -self.duplicados],
            ["Registros limpios finales", self.total_final],
        ]
        return pd.DataFrame(rows, columns=["Paso de limpieza", "Registros"])


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
def load_dataset(source: Any = None) -> pd.DataFrame:
    """Carga el CSV de trabajo.

    Args:
        source: ruta, buffer de Streamlit o ``None``. Si es ``None`` se usa el
            dataset incluido en ``data/peru_localidades.csv``.
    """
    if source is None:
        source = cfg.DEFAULT_DATASET
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"No se encontro el archivo de datos: {path}")
        return pd.read_csv(path)
    return pd.read_csv(source)


def dataset_overview(df: pd.DataFrame, columns: ColumnMap) -> pd.DataFrame:
    """Tabla de exploracion inicial que responde las preguntas de la Actividad 1."""
    lat_col, lon_col = columns.latitude, columns.longitude
    return pd.DataFrame(
        [
            ["a) Cantidad de registros del archivo", f"{len(df):,}"],
            ["b) Cantidad de columnas", f"{len(df.columns)}"],
            ["b) Nombres de las columnas", ", ".join(str(c) for c in df.columns)],
            ["c) Columna de longitud (eje x)", lon_col],
            ["c) Columna de latitud (eje y)", lat_col],
            ["d) Pais seleccionado para el analisis", cfg.DEFAULT_COUNTRY],
        ],
        columns=["Pregunta de la Actividad 1", "Respuesta"],
    )


def column_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Perfil de columnas: tipo, valores no nulos, nulos y ejemplo."""
    rows = []
    for col in df.columns:
        serie = df[col]
        ejemplo = serie.dropna().iloc[0] if serie.notna().any() else ""
        rows.append(
            [
                str(col),
                str(serie.dtype),
                int(serie.notna().sum()),
                int(serie.isna().sum()),
                str(ejemplo)[:40],
            ]
        )
    return pd.DataFrame(
        rows, columns=["Columna", "Tipo", "No nulos", "Nulos", "Valor de ejemplo"]
    )


# ---------------------------------------------------------------------------
# Limpieza (Actividad 2)
# ---------------------------------------------------------------------------
def clean_data(
    df: pd.DataFrame,
    columns: ColumnMap,
    country: str = cfg.DEFAULT_COUNTRY,
) -> tuple[pd.DataFrame, CleaningReport]:
    """Filtra el pais y elimina registros vacios o inconsistentes.

    Pasos aplicados, en orden:

    1. Filtrar por pais seleccionado.
    2. Convertir latitud y longitud a numerico (``errors="coerce"``).
    3. Eliminar filas sin coordenadas.
    4. Eliminar coordenadas imposibles (|lat| > 90 o |lon| > 180).
    5. Eliminar duplicados de ciudad + coordenadas.

    Returns:
        La tabla limpia con nombres de columna canonicos y el reporte de limpieza.
    """
    report = CleaningReport(total_inicial=len(df), pais=country)
    work = df.copy()

    # 1. Filtro de pais
    country_values = work[columns.country].astype(str).str.strip().str.lower()
    work = work[country_values == country.strip().lower()]
    report.sin_pais = report.total_inicial - len(work)
    report.pasos.append(("Filtro de pais", len(work)))

    # 2 y 3. Coordenadas numericas
    work[columns.latitude] = pd.to_numeric(work[columns.latitude], errors="coerce")
    work[columns.longitude] = pd.to_numeric(work[columns.longitude], errors="coerce")
    antes = len(work)
    work = work.dropna(subset=[columns.latitude, columns.longitude])
    report.coordenadas_no_numericas = antes - len(work)
    report.pasos.append(("Coordenadas numericas validas", len(work)))

    # 4. Rango geografico valido
    antes = len(work)
    valid_range = (
        work[columns.latitude].between(-90, 90)
        & work[columns.longitude].between(-180, 180)
    )
    work = work[valid_range]
    report.coordenadas_fuera_de_rango = antes - len(work)
    report.pasos.append(("Coordenadas dentro de rango", len(work)))

    # Renombrado a nombres canonicos
    fields = [columns.city, columns.country, columns.latitude, columns.longitude]
    rename = {
        columns.city: cfg.COL_CITY,
        columns.country: cfg.COL_COUNTRY,
        columns.latitude: cfg.COL_LAT,
        columns.longitude: cfg.COL_LON,
    }
    if columns.region:
        fields.insert(2, columns.region)
        rename[columns.region] = cfg.COL_REGION

    clean = work[fields].rename(columns=rename)
    clean[cfg.COL_CITY] = clean[cfg.COL_CITY].astype(str).str.strip()
    if cfg.COL_REGION in clean.columns:
        clean[cfg.COL_REGION] = clean[cfg.COL_REGION].astype(str).str.strip()

    # 5. Duplicados
    antes = len(clean)
    clean = clean.drop_duplicates(subset=[cfg.COL_CITY, cfg.COL_LAT, cfg.COL_LON])
    report.duplicados = antes - len(clean)
    report.pasos.append(("Sin duplicados", len(clean)))

    sort_cols = [cfg.COL_REGION, cfg.COL_CITY] if cfg.COL_REGION in clean.columns else [cfg.COL_CITY]
    clean = clean.sort_values(sort_cols).reset_index(drop=True)
    report.total_final = len(clean)
    return clean, report


# ---------------------------------------------------------------------------
# Enriquecimiento y filtros
# ---------------------------------------------------------------------------
def add_geo_groups(data: pd.DataFrame) -> pd.DataFrame:
    """Agrega zona macro (Norte/Centro/Sur) y region natural (Costa/Sierra/Selva).

    Si el dataset trae la region administrativa se usa la clasificacion oficial;
    en caso contrario se infiere por latitud y longitud como respaldo.
    """
    grouped = data.copy()
    if cfg.COL_REGION in grouped.columns:
        regions = grouped[cfg.COL_REGION].astype(str).str.strip().str.lower()
    else:
        regions = pd.Series("", index=grouped.index)

    def macro(region: str, lat: float) -> str:
        if region in NORTH_REGIONS:
            return "Norte"
        if region in CENTER_REGIONS:
            return "Centro"
        if region in SOUTH_REGIONS:
            return "Sur"
        if lat <= -13:
            return "Sur"
        if lat <= -8:
            return "Centro"
        return "Norte"

    def natural(region: str, lon: float) -> str:
        if region in JUNGLE_REGIONS:
            return "Selva"
        if region in COAST_REGIONS:
            return "Costa"
        if region in HIGHLAND_REGIONS:
            return "Sierra"
        if lon <= -76:
            return "Costa"
        if lon >= -73.5:
            return "Selva"
        return "Sierra"

    grouped[cfg.COL_MACRO] = [
        macro(region, lat) for region, lat in zip(regions, grouped[cfg.COL_LAT])
    ]
    grouped[cfg.COL_NATURAL] = [
        natural(region, lon) for region, lon in zip(regions, grouped[cfg.COL_LON])
    ]
    return grouped


def filter_geo_data(
    data: pd.DataFrame,
    regions: list[str] | None = None,
    macro_zones: list[str] | None = None,
    natural_regions: list[str] | None = None,
    cities: list[str] | None = None,
) -> pd.DataFrame:
    """Aplica los filtros interactivos. Una lista vacia significa "todos"."""
    filtered = data.copy()
    if regions and cfg.COL_REGION in filtered.columns:
        filtered = filtered[filtered[cfg.COL_REGION].isin(regions)]
    if macro_zones:
        filtered = filtered[filtered[cfg.COL_MACRO].isin(macro_zones)]
    if natural_regions:
        filtered = filtered[filtered[cfg.COL_NATURAL].isin(natural_regions)]
    if cities:
        filtered = filtered[filtered[cfg.COL_CITY].isin(cities)]
    return filtered.reset_index(drop=True)


def available_countries(df: pd.DataFrame, columns: ColumnMap) -> list[str]:
    """Paises presentes en el archivo, ordenados alfabeticamente."""
    values = df[columns.country].dropna().astype(str).str.strip()
    return sorted(v for v in values.unique() if v)


# ---------------------------------------------------------------------------
# Exportacion
# ---------------------------------------------------------------------------
def export_csv(data: pd.DataFrame, path: Path) -> Path:
    """Guarda un DataFrame como CSV UTF-8 creando la carpeta si hace falta."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False, encoding="utf-8")
    return path


def to_geojson(data: pd.DataFrame) -> dict:
    """Convierte la tabla limpia a GeoJSON FeatureCollection (EPSG:4326)."""
    features = []
    for _, row in data.iterrows():
        properties = {
            key: (None if pd.isna(value) else value)
            for key, value in row.items()
            if key not in (cfg.COL_LAT, cfg.COL_LON)
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row[cfg.COL_LON]), float(row[cfg.COL_LAT])],
                },
                "properties": properties,
            }
        )
    return {"type": "FeatureCollection", "features": features}
