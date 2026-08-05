"""Mapas interactivos sobre cartografia real (OpenStreetMap, sin token).

Valor agregado sobre lo minimo que pide la practica: las mismas tres
visualizaciones (puntos, cuadricula y malla) se proyectan sobre el mapa real
del territorio, de modo que se puede verificar que el dominio calculado
coincide con la geografia del pais analizado.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import config as cfg
from .charts import HOVER_REAL, _hover_text
from .domain import GeoDomain, Grid

MAP_HEIGHT = 680
HOVER_MAP = HOVER_REAL.replace("%{x:.4f}", "%{lon:.4f}").replace("%{y:.4f}", "%{lat:.4f}")


def _zoom_for(domain: GeoDomain) -> float:
    """Zoom aproximado segun la amplitud del dominio."""
    span = max(domain.width, domain.height, 0.05)
    if span > 12:
        return 4.0
    if span > 6:
        return 4.8
    if span > 3:
        return 5.8
    if span > 1.5:
        return 6.8
    if span > 0.6:
        return 8.0
    return 9.5


def _layout(fig: go.Figure, title: str, domain: GeoDomain) -> go.Figure:
    lon_center, lat_center = domain.center
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        height=MAP_HEIGHT,
        margin=dict(l=0, r=0, t=62, b=0),
        mapbox=dict(
            style="open-street-map",
            center={"lat": lat_center, "lon": lon_center},
            zoom=_zoom_for(domain),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color=cfg.PALETTE["ink"]),
        legend=dict(orientation="h", y=1.02, x=0.01, bgcolor="rgba(255,255,255,.9)"),
    )
    return fig


def _real_points_trace(data: pd.DataFrame, size: int = 12) -> go.Scattermapbox:
    return go.Scattermapbox(
        lat=data[cfg.COL_LAT],
        lon=data[cfg.COL_LON],
        mode="markers",
        name="Puntos reales",
        text=data[cfg.COL_CITY],
        customdata=_hover_text(data),
        hovertemplate=HOVER_MAP,
        marker=dict(size=size, color=cfg.PALETTE["real"], opacity=0.9),
    )


def _domain_trace(domain: GeoDomain) -> go.Scattermapbox:
    lons, lats = domain.rectangle()
    return go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode="lines",
        name="Dominio D",
        line=dict(color=cfg.PALETTE["domain"], width=3),
        hoverinfo="skip",
    )


def map_points(data: pd.DataFrame, domain: GeoDomain, country: str) -> go.Figure:
    """Localidades reales sobre el mapa, agrupadas por region natural."""
    fig = go.Figure()
    if cfg.COL_NATURAL in data.columns:
        for name, group in data.groupby(cfg.COL_NATURAL):
            fig.add_trace(
                go.Scattermapbox(
                    lat=group[cfg.COL_LAT],
                    lon=group[cfg.COL_LON],
                    mode="markers",
                    name=str(name),
                    text=group[cfg.COL_CITY],
                    customdata=_hover_text(group),
                    hovertemplate=HOVER_MAP,
                    marker=dict(
                        size=13,
                        color=cfg.NATURAL_REGION_COLORS.get(str(name), cfg.PALETTE["real"]),
                        opacity=0.88,
                    ),
                )
            )
    else:
        fig.add_trace(_real_points_trace(data, size=13))
    fig.add_trace(_domain_trace(domain))
    return _layout(fig, f"Mapa de localidades y dominio - {country}", domain)


def map_grid(data: pd.DataFrame, grid: Grid, country: str) -> go.Figure:
    """Cuadricula generada proyectada sobre el mapa real."""
    fig = go.Figure()
    fig.add_trace(
        go.Scattermapbox(
            lat=grid.Y.ravel(),
            lon=grid.X.ravel(),
            mode="markers",
            name=f"Cuadricula ({grid.size:,} nodos)",
            marker=dict(size=6, color=cfg.PALETTE["generated"], opacity=0.65),
            hovertemplate="Nodo generado<br>Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<extra></extra>",
        )
    )
    fig.add_trace(_real_points_trace(data, size=11))
    fig.add_trace(_domain_trace(grid.domain))
    return _layout(fig, f"Cuadricula geografica sobre el mapa - {country}", grid.domain)


def map_mesh(data: pd.DataFrame, grid: Grid, country: str) -> go.Figure:
    """Malla de lineas sobre el mapa real, con el dominio y los puntos reales."""
    fig = go.Figure()
    line_lat: list[float | None] = []
    line_lon: list[float | None] = []
    for i in range(grid.ny):
        line_lat.extend([*grid.Y[i, :].tolist(), None])
        line_lon.extend([*grid.X[i, :].tolist(), None])
    for j in range(grid.nx):
        line_lat.extend([*grid.Y[:, j].tolist(), None])
        line_lon.extend([*grid.X[:, j].tolist(), None])
    fig.add_trace(
        go.Scattermapbox(
            lat=line_lat,
            lon=line_lon,
            mode="lines",
            name="Malla (lineas H y V)",
            line=dict(color="rgba(47, 158, 68, 0.6)", width=1.5),
            hoverinfo="skip",
        )
    )
    fig.add_trace(_domain_trace(grid.domain))
    fig.add_trace(_real_points_trace(data, size=12))
    return _layout(fig, f"Malla geografica sobre el mapa - {country}", grid.domain)
