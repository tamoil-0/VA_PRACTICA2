"""Graficos cartesianos interactivos con Plotly (Actividades 4, 5 y 6).

Son la version interactiva de las figuras de ``figures.py``: mismos datos,
misma paleta y mismos ejes (longitud en X, latitud en Y), pero con hover,
zoom y leyenda para explorar el dominio dentro de la app.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from . import config as cfg
from .analysis import cell_occupancy
from .domain import GeoDomain, Grid

CHART_HEIGHT = 620


def _style(fig: go.Figure, title: str, domain: GeoDomain, margin: float = 0.8) -> go.Figure:
    """Aplica el estilo comun: titulo, etiquetas de ejes, cuadricula y escala 1:1."""
    view = domain.padded(margin)
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        height=CHART_HEIGHT,
        margin=dict(l=50, r=25, t=70, b=45),
        plot_bgcolor=cfg.PALETTE["surface"],
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color=cfg.PALETTE["ink"]),
        legend=dict(orientation="h", y=1.04, x=0.0, bgcolor="rgba(255,255,255,.85)"),
        hovermode="closest",
    )
    fig.update_xaxes(
        title="Longitud (x)",
        range=[view.xmin, view.xmax],
        showgrid=True,
        gridcolor=cfg.PALETTE["grid"],
        zeroline=False,
    )
    fig.update_yaxes(
        title="Latitud (y)",
        range=[view.ymin, view.ymax],
        showgrid=True,
        gridcolor=cfg.PALETTE["grid"],
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
    )
    return fig


def _domain_shape(fig: go.Figure, domain: GeoDomain) -> None:
    fig.add_shape(
        type="rect",
        x0=domain.xmin,
        x1=domain.xmax,
        y0=domain.ymin,
        y1=domain.ymax,
        line=dict(color=cfg.PALETTE["domain"], width=2),
        fillcolor="rgba(0,0,0,0)",
    )


def _hover_text(data: pd.DataFrame) -> np.ndarray:
    """Columnas auxiliares para el hover: region, zona macro y region natural."""
    empty = pd.Series("", index=data.index)
    return np.stack(
        [
            data.get(cfg.COL_REGION, empty).astype(str),
            data.get(cfg.COL_MACRO, empty).astype(str),
            data.get(cfg.COL_NATURAL, empty).astype(str),
        ],
        axis=-1,
    )


HOVER_REAL = (
    "<b>%{text}</b><br>Region: %{customdata[0]}"
    "<br>Zona macro: %{customdata[1]}<br>Region natural: %{customdata[2]}"
    "<br>Longitud: %{x:.4f}<br>Latitud: %{y:.4f}<extra></extra>"
)


# ---------------------------------------------------------------------------
# Actividad 4
# ---------------------------------------------------------------------------
def chart_points(data: pd.DataFrame, domain: GeoDomain, country: str) -> go.Figure:
    """Dispersion de puntos reales, coloreada por region natural si existe."""
    fig = go.Figure()
    if cfg.COL_NATURAL in data.columns:
        for name, group in data.groupby(cfg.COL_NATURAL):
            fig.add_trace(
                go.Scatter(
                    x=group[cfg.COL_LON],
                    y=group[cfg.COL_LAT],
                    mode="markers",
                    name=str(name),
                    text=group[cfg.COL_CITY],
                    customdata=_hover_text(group),
                    hovertemplate=HOVER_REAL,
                    marker=dict(
                        size=11,
                        color=cfg.NATURAL_REGION_COLORS.get(str(name), cfg.PALETTE["real"]),
                        line=dict(width=1, color="#ffffff"),
                        opacity=0.9,
                    ),
                )
            )
    else:
        fig.add_trace(
            go.Scatter(
                x=data[cfg.COL_LON],
                y=data[cfg.COL_LAT],
                mode="markers",
                name="Puntos reales",
                text=data[cfg.COL_CITY],
                customdata=_hover_text(data),
                hovertemplate=HOVER_REAL,
                marker=dict(size=11, color=cfg.PALETTE["real"], line=dict(width=1, color="#fff")),
            )
        )
    _domain_shape(fig, domain)
    return _style(fig, f"Puntos geograficos reales - {country}", domain)


# ---------------------------------------------------------------------------
# Actividad 5
# ---------------------------------------------------------------------------
def chart_grid(grid: Grid, country: str) -> go.Figure:
    """Cuadricula de puntos generados dentro del dominio."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=grid.X.ravel(),
            y=grid.Y.ravel(),
            mode="markers",
            name=f"Cuadricula generada ({grid.size:,} puntos)",
            marker=dict(size=6, color=cfg.PALETTE["generated"], opacity=0.75),
            hovertemplate="Nodo generado<br>Longitud: %{x:.2f}<br>Latitud: %{y:.2f}<extra></extra>",
        )
    )
    _domain_shape(fig, grid.domain)
    return _style(
        fig,
        f"Cuadricula de puntos del dominio - {country} (dx = {grid.dx}, dy = {grid.dy})",
        grid.domain,
    )


# ---------------------------------------------------------------------------
# Actividad 6
# ---------------------------------------------------------------------------
def chart_mesh(data: pd.DataFrame, grid: Grid, country: str) -> go.Figure:
    """Malla visual: lineas horizontales y verticales mas puntos reales.

    Las lineas se envian como un unico trace con separadores ``None`` para no
    crear cientos de traces (mucho mas rapido de renderizar en el navegador).
    """
    fig = go.Figure()
    line_x: list[float | None] = []
    line_y: list[float | None] = []
    for i in range(grid.ny):
        line_x.extend([*grid.X[i, :].tolist(), None])
        line_y.extend([*grid.Y[i, :].tolist(), None])
    for j in range(grid.nx):
        line_x.extend([*grid.X[:, j].tolist(), None])
        line_y.extend([*grid.Y[:, j].tolist(), None])
    fig.add_trace(
        go.Scatter(
            x=line_x,
            y=line_y,
            mode="lines",
            name="Malla (lineas H y V)",
            line=dict(color="rgba(47, 158, 68, 0.45)", width=1),
            hoverinfo="skip",
        )
    )
    _domain_shape(fig, grid.domain)
    fig.add_trace(
        go.Scatter(
            x=data[cfg.COL_LON],
            y=data[cfg.COL_LAT],
            mode="markers",
            name="Puntos reales superpuestos",
            text=data[cfg.COL_CITY],
            customdata=_hover_text(data),
            hovertemplate=HOVER_REAL,
            marker=dict(size=10, color=cfg.PALETTE["real"], line=dict(width=1, color="#ffffff")),
        )
    )
    return _style(
        fig, f"Malla visual del dominio con puntos reales - {country}", grid.domain
    )


# ---------------------------------------------------------------------------
# Analisis adicional
# ---------------------------------------------------------------------------
def chart_density(data: pd.DataFrame, grid: Grid, country: str) -> go.Figure:
    """Mapa de calor de localidades por celda de la malla."""
    occupancy = cell_occupancy(data, grid)
    fig = go.Figure()
    if occupancy.counts.size:
        counts = occupancy.counts.astype(float)
        counts[counts == 0] = np.nan
        # El heatmap se ancla en el centro de cada celda de la malla.
        x_centers = (grid.x_lines[:-1] + grid.x_lines[1:]) / 2
        y_centers = (grid.y_lines[:-1] + grid.y_lines[1:]) / 2
        fig.add_trace(
            go.Heatmap(
                x=x_centers,
                y=y_centers,
                z=counts,
                xgap=1,
                ygap=1,
                colorscale="YlGnBu",
                colorbar=dict(title="Localidades"),
                hovertemplate="Longitud: %{x:.2f}<br>Latitud: %{y:.2f}<br>Localidades: %{z}<extra></extra>",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=data[cfg.COL_LON],
            y=data[cfg.COL_LAT],
            mode="markers",
            name="Puntos reales",
            text=data[cfg.COL_CITY],
            customdata=_hover_text(data),
            hovertemplate=HOVER_REAL,
            marker=dict(size=7, color=cfg.PALETTE["ink"], opacity=0.75),
        )
    )
    _domain_shape(fig, grid.domain)
    return _style(fig, f"Densidad de localidades por celda - {country}", grid.domain)
