"""Configuracion central del proyecto.

Aqui viven las rutas, los metadatos academicos, la paleta de colores y los
nombres canonicos de columnas. Ningun otro modulo define constantes propias:
todos importan desde aqui para que el proyecto tenga una sola fuente de verdad.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
DOCS_DIR = PROJECT_ROOT / "docs"
FIGURES_DIR = DOCS_DIR / "figuras"
CAPTURES_DIR = DOCS_DIR / "capturas"
REPORT_DIR = PROJECT_ROOT / "informe"
EXPORTS_DIR = PROJECT_ROOT / "salidas"

DEFAULT_DATASET = DATA_DIR / "peru_localidades.csv"
LOGO_UNAP = ASSETS_DIR / "logo_unap.png"
LOGO_EPISI = ASSETS_DIR / "logo_episi.png"
REPORT_FILENAME = "INFORME_PRACTICA_02.pdf"

# ---------------------------------------------------------------------------
# Metadatos academicos (aparecen en la caratula del informe y en la app)
# ---------------------------------------------------------------------------
STUDENT_NAME = "Jhon Marco Aracayo Mamani"
UNIVERSITY = "Universidad Nacional del Altiplano - Puno"
FACULTY = "Facultad de Ingenieria Mecanica Electrica, Electronica y Sistemas"
PROGRAM = "Escuela Profesional de Ingenieria de Sistemas"
COURSE = "Visualizacion de Datos"
SEMESTER = "X"
UNIT = "Unidad 2 - Tecnicas de modelado de dominios"
PRACTICE_TITLE = "Practica Calificada N.o 02"
PRACTICE_SUBTITLE = (
    "Visualizacion de dominios geograficos mediante puntos, cuadriculas y mallas"
)
TOTAL_POINTS = 20

DATASET_NAME = "Geolocation Data [Longitude Latitude]"
DATASET_SOURCE = "Kaggle"
DATASET_URL = "https://www.kaggle.com/datasets/liewyousheng/geolocation"
REPO_URL = "https://github.com/tamoil-0/VA_PRACTICA2"

DEFAULT_COUNTRY = "Peru"
DEFAULT_DX = 0.5
DEFAULT_DY = 0.5

# ---------------------------------------------------------------------------
# Nombres canonicos de columnas despues de la limpieza
# ---------------------------------------------------------------------------
COL_CITY = "Ciudad o localidad"
COL_COUNTRY = "Pais"
COL_REGION = "Region"
COL_LAT = "Latitud"
COL_LON = "Longitud"
COL_MACRO = "Zona macro"
COL_NATURAL = "Region natural"

CLEAN_COLUMNS = [COL_CITY, COL_COUNTRY, COL_REGION, COL_LAT, COL_LON]

# ---------------------------------------------------------------------------
# Deteccion automatica de columnas en CSV heterogeneos
# ---------------------------------------------------------------------------
CITY_CANDIDATES = ["city_name", "city", "name", "locality", "municipality", "town"]
COUNTRY_CANDIDATES = ["country_name", "country", "country_code", "pais"]
LAT_CANDIDATES = ["latitude", "lat", "y", "gps_latitude"]
LON_CANDIDATES = ["longitude", "lng", "lon", "long", "x", "gps_longitude"]
REGION_CANDIDATES = [
    "region_name",
    "state_name",
    "admin_name",
    "province",
    "department",
    "departamento",
]

# ---------------------------------------------------------------------------
# Paleta unica para Plotly, Matplotlib y el PDF
# ---------------------------------------------------------------------------
PALETTE = {
    "ink": "#132238",
    "muted": "#5e6c7a",
    "line": "#d9e2ec",
    "panel": "#ffffff",
    "grid": "#dbe6ee",
    "surface": "#fbfdff",
    "real": "#0b7285",      # puntos reales
    "generated": "#e8590c",  # puntos de la cuadricula
    "mesh": "#2f9e44",       # lineas de la malla
    "domain": "#132238",     # rectangulo del dominio
}

NATURAL_REGION_COLORS = {
    "Costa": "#0b7285",
    "Sierra": "#e8590c",
    "Selva": "#2f9e44",
}

# Radio medio de la Tierra en kilometros (para distancias haversine).
EARTH_RADIUS_KM = 6371.0088
