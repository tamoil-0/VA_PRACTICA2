"""Paquete de la Practica Calificada 02 - Visualizacion de dominios geograficos.

Organizacion de los modulos (cada uno resuelve una parte de la practica):

===================  =====================================================
Modulo               Responsabilidad
===================  =====================================================
``config``           Rutas, metadatos academicos, paleta y constantes.
``domain``           ColumnMap, GeoDomain y Grid (Actividades 1 y 3).
``dataio``           Carga, exploracion, limpieza y filtros (Act. 1 y 2).
``analysis``         Metricas de densidad, distancias y resolucion (Act. 7).
``figures``          Figuras estaticas Matplotlib (Act. 4, 5 y 6).
``charts``           Graficos cartesianos interactivos con Plotly.
``maps``             Mapas sobre cartografia real (valor agregado).
``content``          Interpretaciones, respuestas y conclusiones.
``pipeline``         Orquestador: ejecuta las 7 actividades de una vez.
``report``           Informe PDF final.
``ui``               Interfaz Streamlit (tema y pestanas).
===================  =====================================================

Uso rapido::

    from vizdominios import run_analysis, save_report

    resultado = run_analysis(country="Peru", dx=0.5, dy=0.5)
    save_report(resultado)
"""

from __future__ import annotations

from . import analysis, charts, config, content, dataio, domain, figures, maps, report
from .domain import ColumnMap, GeoDomain, Grid, detect_columns
from .pipeline import AnalysisResult, EmptySelectionError, run_analysis
from .report import build_report, save_report

__version__ = "2.0.0"

__all__ = [
    "AnalysisResult",
    "ColumnMap",
    "EmptySelectionError",
    "GeoDomain",
    "Grid",
    "analysis",
    "build_report",
    "charts",
    "config",
    "content",
    "dataio",
    "detect_columns",
    "domain",
    "figures",
    "maps",
    "report",
    "run_analysis",
    "save_report",
]
