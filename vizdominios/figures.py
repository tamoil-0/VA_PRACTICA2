"""Figuras estaticas con Matplotlib (Actividades 4, 5 y 6).

Estas figuras son las que se insertan en el informe PDF y las que ``main.py``
guarda como PNG en ``docs/figuras/``. Se usa el backend ``Agg`` para poder
generarlas sin interfaz grafica (por ejemplo dentro de un servidor o de CI).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (debe importarse despues de use)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import config as cfg  # noqa: E402
from .analysis import cell_occupancy  # noqa: E402
from .domain import GeoDomain, Grid  # noqa: E402

FIGSIZE = (8.6, 6.2)
DPI = 170


# ---------------------------------------------------------------------------
# Utilidades comunes
# ---------------------------------------------------------------------------
def _base_axes(domain: GeoDomain, title: str, margin: float = 0.8):
    """Crea figura y ejes con titulo, etiquetas, limites y cuadricula de fondo.

    Todas las figuras comparten este armazon para cumplir los requisitos de la
    practica: longitud en X, latitud en Y, titulo descriptivo, etiquetas de
    ejes y cuadricula de fondo.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    view = domain.padded(margin)
    ax.set_facecolor(cfg.PALETTE["surface"])
    ax.grid(True, color=cfg.PALETTE["grid"], linewidth=0.8, zorder=0)
    ax.set_xlim(view.xmin, view.xmax)
    ax.set_ylim(view.ymin, view.ymax)
    ax.set_xlabel("Longitud (x)", fontsize=10)
    ax.set_ylabel("Latitud (y)", fontsize=10)
    ax.set_title(title, fontsize=12, color=cfg.PALETTE["ink"], pad=12)
    ax.set_aspect("equal", adjustable="box")
    for spine in ax.spines.values():
        spine.set_color(cfg.PALETTE["line"])
    return fig, ax


def _draw_domain_rectangle(ax, domain: GeoDomain, label: str = "Dominio D") -> None:
    ax.add_patch(
        plt.Rectangle(
            (domain.xmin, domain.ymin),
            domain.width,
            domain.height,
            fill=False,
            edgecolor=cfg.PALETTE["domain"],
            linewidth=1.6,
            zorder=4,
            label=label,
        )
    )


def render_png(fig) -> BytesIO:
    """Serializa la figura a PNG en memoria (para ReportLab o Streamlit)."""
    buffer = BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", facecolor="white")
    plt.close(fig)
    buffer.seek(0)
    return buffer


def save_png(fig, path: Path) -> Path:
    """Guarda la figura en disco y la cierra."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, format="png", facecolor="white")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Actividad 4: puntos geograficos reales
# ---------------------------------------------------------------------------
def fig_points(data: pd.DataFrame, domain: GeoDomain, country: str):
    """Grafico de dispersion de las coordenadas reales."""
    fig, ax = _base_axes(domain, f"Puntos geograficos reales - {country}")
    if cfg.COL_NATURAL in data.columns:
        for name, group in data.groupby(cfg.COL_NATURAL):
            ax.scatter(
                group[cfg.COL_LON],
                group[cfg.COL_LAT],
                s=30,
                color=cfg.NATURAL_REGION_COLORS.get(str(name), cfg.PALETTE["real"]),
                edgecolor="white",
                linewidth=0.6,
                label=str(name),
                zorder=3,
            )
    else:
        ax.scatter(
            data[cfg.COL_LON],
            data[cfg.COL_LAT],
            s=30,
            color=cfg.PALETTE["real"],
            edgecolor="white",
            linewidth=0.6,
            label="Localidades",
            zorder=3,
        )
    _draw_domain_rectangle(ax, domain)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.92)
    return fig


# ---------------------------------------------------------------------------
# Actividad 5: cuadricula de puntos
# ---------------------------------------------------------------------------
def fig_grid(grid: Grid, country: str):
    """Puntos generados regularmente dentro del dominio."""
    domain = grid.domain
    fig, ax = _base_axes(
        domain,
        f"Cuadricula de puntos del dominio - {country} (dx = {grid.dx}, dy = {grid.dy})",
    )
    ax.scatter(
        grid.X.ravel(),
        grid.Y.ravel(),
        s=12,
        color=cfg.PALETTE["generated"],
        alpha=0.8,
        label=f"Cuadricula generada ({grid.size:,} puntos)",
        zorder=3,
    )
    _draw_domain_rectangle(ax, domain)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.92)
    return fig


# ---------------------------------------------------------------------------
# Actividad 6: malla visual
# ---------------------------------------------------------------------------
def fig_mesh(data: pd.DataFrame, grid: Grid, country: str):
    """Malla de lineas horizontales y verticales con los puntos reales encima."""
    domain = grid.domain
    fig, ax = _base_axes(domain, f"Malla visual del dominio con puntos reales - {country}")
    for i in range(grid.ny):
        ax.plot(
            grid.X[i, :],
            grid.Y[i, :],
            color=cfg.PALETTE["mesh"],
            linewidth=0.7,
            alpha=0.55,
            zorder=1,
        )
    for j in range(grid.nx):
        ax.plot(
            grid.X[:, j],
            grid.Y[:, j],
            color=cfg.PALETTE["mesh"],
            linewidth=0.7,
            alpha=0.55,
            zorder=1,
        )
    ax.plot([], [], color=cfg.PALETTE["mesh"], linewidth=1.4, label="Malla (lineas H y V)")
    _draw_domain_rectangle(ax, domain)
    ax.scatter(
        data[cfg.COL_LON],
        data[cfg.COL_LAT],
        s=28,
        color=cfg.PALETTE["real"],
        edgecolor="white",
        linewidth=0.6,
        label="Puntos reales superpuestos",
        zorder=3,
    )
    ax.legend(loc="upper right", fontsize=8, framealpha=0.92)
    return fig


# ---------------------------------------------------------------------------
# Analisis adicional: densidad por celda
# ---------------------------------------------------------------------------
def fig_density(data: pd.DataFrame, grid: Grid, country: str):
    """Mapa de calor con el numero de localidades por celda de la malla."""
    domain = grid.domain
    occupancy = cell_occupancy(data, grid)
    fig, ax = _base_axes(domain, f"Densidad de localidades por celda - {country}")
    if occupancy.counts.size:
        masked = np.ma.masked_where(occupancy.counts == 0, occupancy.counts)
        mesh = ax.pcolormesh(
            grid.x_lines,
            grid.y_lines,
            masked,
            cmap="YlGnBu",
            edgecolors=cfg.PALETTE["grid"],
            linewidth=0.3,
            zorder=2,
        )
        bar = fig.colorbar(mesh, ax=ax, shrink=0.85)
        bar.set_label("Localidades por celda", fontsize=9)
    ax.scatter(
        data[cfg.COL_LON],
        data[cfg.COL_LAT],
        s=12,
        color=cfg.PALETTE["domain"],
        alpha=0.7,
        label="Puntos reales",
        zorder=3,
    )
    _draw_domain_rectangle(ax, domain)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.92)
    return fig


# ---------------------------------------------------------------------------
# Analisis adicional: efecto de dx y dy (preguntas 5 y 6)
# ---------------------------------------------------------------------------
def fig_resolution_panel(
    data: pd.DataFrame,
    domain: GeoDomain,
    deltas: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0),
):
    """Panel comparativo de la misma malla con distintos pasos dx = dy."""
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.6), dpi=DPI)
    view = domain.padded(0.6)
    for ax, delta in zip(axes.ravel(), deltas):
        grid = Grid.from_domain(domain, delta, delta)
        ax.set_facecolor(cfg.PALETTE["surface"])
        for i in range(grid.ny):
            ax.plot(grid.X[i, :], grid.Y[i, :], color=cfg.PALETTE["mesh"], linewidth=0.5, alpha=0.5)
        for j in range(grid.nx):
            ax.plot(grid.X[:, j], grid.Y[:, j], color=cfg.PALETTE["mesh"], linewidth=0.5, alpha=0.5)
        ax.scatter(
            data[cfg.COL_LON],
            data[cfg.COL_LAT],
            s=8,
            color=cfg.PALETTE["real"],
            alpha=0.85,
            zorder=3,
        )
        ax.set_xlim(view.xmin, view.xmax)
        ax.set_ylim(view.ymin, view.ymax)
        ax.set_title(
            f"dx = dy = {delta}  |  {grid.size:,} puntos",
            fontsize=10,
            color=cfg.PALETTE["ink"],
        )
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal", adjustable="box")
    fig.suptitle(
        "Efecto de la resolucion de la cuadricula sobre la lectura visual",
        fontsize=12,
        color=cfg.PALETTE["ink"],
    )
    return fig
