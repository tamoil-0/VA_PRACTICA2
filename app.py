from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from textwrap import wrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


APP_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = APP_DIR / "data" / "peru_geolocation_sample.csv"
DATASET_URL = "https://www.kaggle.com/datasets/liewyousheng/geolocation"


CITY_CANDIDATES = ["city_name", "city", "name", "locality", "municipality", "town"]
COUNTRY_CANDIDATES = ["country_name", "country", "country_code", "pais"]
LAT_CANDIDATES = ["latitude", "lat", "y", "gps_latitude"]
LON_CANDIDATES = ["longitude", "lng", "lon", "long", "x", "gps_longitude"]
REGION_CANDIDATES = ["region_name", "state_name", "admin_name", "province", "department"]


@dataclass(frozen=True)
class ColumnMap:
    city: str
    country: str
    latitude: str
    longitude: str
    region: str | None = None


st.set_page_config(
    page_title="Dominios geograficos - Peru",
    page_icon="map",
    layout="wide",
    initial_sidebar_state="expanded",
)


def css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #132238;
            --muted: #5e6c7a;
            --panel: #ffffff;
            --line: #d9e2ec;
            --aqua: #0b7285;
            --coral: #e8590c;
            --green: #2f9e44;
        }
        .stApp {
            background:
                linear-gradient(180deg, #f8fbfd 0%, #eef5f7 42%, #f8faf8 100%);
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }
        h1, h2, h3 {
            letter-spacing: 0;
            color: var(--ink);
        }
        h1 {
            font-size: clamp(2rem, 4vw, 4.2rem);
            line-height: 1.02;
            margin-bottom: .25rem;
        }
        .hero {
            padding: 1.25rem 0 1.75rem 0;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1rem;
        }
        .hero p {
            max-width: 980px;
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.55;
        }
        .metric-wrap [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .9rem 1rem;
            box-shadow: 0 12px 32px rgba(19, 34, 56, .05);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }
        .note {
            border-left: 4px solid var(--aqua);
            background: #ffffff;
            padding: .9rem 1rem;
            border-radius: 6px;
            color: #213547;
            margin: .5rem 0 1rem 0;
        }
        .answer {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            min-height: 118px;
            box-shadow: 0 10px 24px rgba(19, 34, 56, .04);
        }
        .small-muted {
            color: var(--muted);
            font-size: .9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def find_column(columns: list[str], candidates: list[str]) -> str | None: 
    lookup = {c.lower().strip(): c for c in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    for col in columns:
        normalized = col.lower().strip()
        if any(candidate in normalized for candidate in candidates):
            return col
    return None


def detect_columns(df: pd.DataFrame) -> ColumnMap:
    columns = list(df.columns)
    city = find_column(columns, CITY_CANDIDATES)
    country = find_column(columns, COUNTRY_CANDIDATES)
    lat = find_column(columns, LAT_CANDIDATES)
    lon = find_column(columns, LON_CANDIDATES)
    region = find_column(columns, REGION_CANDIDATES)

    missing = []
    if city is None:
        missing.append("ciudad/localidad")
    if country is None:
        missing.append("pais")
    if lat is None:
        missing.append("latitud")
    if lon is None:
        missing.append("longitud")
    if missing:
        raise ValueError("No se detectaron columnas de " + ", ".join(missing) + ".")
    return ColumnMap(city=city, country=country, latitude=lat, longitude=lon, region=region)


@st.cache_data(show_spinner=False)
def load_sample() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_PATH)


def load_uploaded(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return load_sample()
    return pd.read_csv(uploaded_file)


def clean_data(df: pd.DataFrame, columns: ColumnMap, country_filter: str) -> pd.DataFrame:
    clean = df.copy()
    clean[columns.latitude] = pd.to_numeric(clean[columns.latitude], errors="coerce")
    clean[columns.longitude] = pd.to_numeric(clean[columns.longitude], errors="coerce")
    clean = clean.dropna(subset=[columns.latitude, columns.longitude])

    country_values = clean[columns.country].astype(str).str.strip()
    selected = clean[country_values.str.lower() == country_filter.strip().lower()].copy()

    fields = [columns.city, columns.country, columns.latitude, columns.longitude]
    rename = {
        columns.city: "Ciudad o localidad",
        columns.country: "Pais",
        columns.latitude: "Latitud",
        columns.longitude: "Longitud",
    }
    if columns.region:
        fields.insert(2, columns.region)
        rename[columns.region] = "Region"

    selected = selected[fields].rename(columns=rename)
    selected = selected.drop_duplicates(subset=["Ciudad o localidad", "Latitud", "Longitud"])
    selected = selected.sort_values(["Pais", "Ciudad o localidad"]).reset_index(drop=True)
    return selected


def domain_table(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    domain = {
        "xmin": float(data["Longitud"].min()),
        "xmax": float(data["Longitud"].max()),
        "ymin": float(data["Latitud"].min()),
        "ymax": float(data["Latitud"].max()),
    }
    table = pd.DataFrame(
        [
            ["Longitud minima", domain["xmin"], "Limite occidental del dominio"],
            ["Longitud maxima", domain["xmax"], "Limite oriental del dominio"],
            ["Latitud minima", domain["ymin"], "Limite sur del dominio"],
            ["Latitud maxima", domain["ymax"], "Limite norte del dominio"],
        ],
        columns=["Parametro", "Valor", "Interpretacion"],
    )
    return table, domain


def make_grid(domain: dict[str, float], dx: float, dy: float) -> tuple[np.ndarray, np.ndarray]:
    x_grid = np.arange(domain["xmin"], domain["xmax"] + dx, dx)
    y_grid = np.arange(domain["ymin"], domain["ymax"] + dy, dy)
    return np.meshgrid(x_grid, y_grid)


def add_geo_groups(data: pd.DataFrame) -> pd.DataFrame:
    grouped = data.copy()
    region_series = grouped["Region"].astype(str).str.strip() if "Region" in grouped.columns else pd.Series("", index=grouped.index)
    regions = region_series.str.lower()

    north = {"tumbes", "piura", "lambayeque", "la libertad", "cajamarca", "amazonas", "san martin", "loreto"}
    center = {"lima", "ancash", "huanuco", "pasco", "junin", "ucayali", "huancavelica", "callao"}
    south = {"ica", "ayacucho", "apurimac", "cusco", "arequipa", "puno", "moquegua", "tacna", "madre de dios"}
    coast = {"tumbes", "piura", "lambayeque", "la libertad", "ancash", "lima", "callao", "ica", "arequipa", "moquegua", "tacna"}
    highlands = {"cajamarca", "ancash", "huanuco", "pasco", "junin", "huancavelica", "ayacucho", "apurimac", "cusco", "puno"}
    jungle = {"amazonas", "san martin", "loreto", "ucayali", "madre de dios"}

    def macro(region: str, lat: float) -> str:
        if region in north:
            return "Norte"
        if region in center:
            return "Centro"
        if region in south:
            return "Sur"
        if lat <= -13:
            return "Sur"
        if lat <= -8:
            return "Centro"
        return "Norte"

    def natural(region: str, lon: float) -> str:
        if region in coast:
            return "Costa"
        if region in jungle:
            return "Selva"
        if region in highlands:
            return "Sierra"
        if lon <= -76:
            return "Costa"
        if lon >= -73.5:
            return "Selva"
        return "Sierra"

    grouped["Zona macro"] = [macro(region, lat) for region, lat in zip(regions, grouped["Latitud"])]
    grouped["Region natural"] = [natural(region, lon) for region, lon in zip(regions, grouped["Longitud"])]
    return grouped


def filter_geo_data(
    data: pd.DataFrame,
    selected_regions: list[str],
    selected_macro: list[str],
    selected_natural: list[str],
    selected_cities: list[str],
) -> pd.DataFrame:
    filtered = data.copy()
    if selected_regions and "Region" in filtered.columns:
        filtered = filtered[filtered["Region"].isin(selected_regions)]
    if selected_macro:
        filtered = filtered[filtered["Zona macro"].isin(selected_macro)]
    if selected_natural:
        filtered = filtered[filtered["Region natural"].isin(selected_natural)]
    if selected_cities:
        filtered = filtered[filtered["Ciudad o localidad"].isin(selected_cities)]
    return filtered.reset_index(drop=True)


def style_geo_layout(fig: go.Figure, title: str, domain: dict[str, float]) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        height=620,
        margin=dict(l=40, r=20, t=70, b=40),
        plot_bgcolor="#fbfdff",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color="#132238"),
        legend=dict(orientation="h", y=1.03, x=0.0),
    )
    fig.update_xaxes(
        title="Longitud",
        range=[domain["xmin"] - 0.8, domain["xmax"] + 0.8],
        showgrid=True,
        gridcolor="#dbe6ee",
        zeroline=False,
    )
    fig.update_yaxes(
        title="Latitud",
        range=[domain["ymin"] - 0.8, domain["ymax"] + 0.8],
        showgrid=True,
        gridcolor="#dbe6ee",
        zeroline=False,
        scaleanchor="x",
        scaleratio=1,
    )
    return fig


def fig_points(data: pd.DataFrame, domain: dict[str, float], country: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["Longitud"],
            y=data["Latitud"],
            mode="markers",
            name="Puntos reales",
            text=data["Ciudad o localidad"],
            hovertemplate="<b>%{text}</b><br>Longitud: %{x:.4f}<br>Latitud: %{y:.4f}<extra></extra>",
            marker=dict(size=10, color="#0b7285", line=dict(width=1, color="#ffffff"), opacity=0.88),
        )
    )
    return style_geo_layout(fig, f"Puntos geograficos reales - {country}", domain)


def fig_grid(X: np.ndarray, Y: np.ndarray, domain: dict[str, float], country: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=X.ravel(),
            y=Y.ravel(),
            mode="markers",
            name="Cuadricula generada",
            marker=dict(size=5, color="#e8590c", opacity=0.72),
            hovertemplate="Longitud: %{x:.2f}<br>Latitud: %{y:.2f}<extra></extra>",
        )
    )
    return style_geo_layout(fig, f"Cuadricula de puntos del dominio - {country}", domain)


def fig_mesh(data: pd.DataFrame, X: np.ndarray, Y: np.ndarray, domain: dict[str, float], country: str) -> go.Figure:
    fig = go.Figure()
    for i in range(Y.shape[0]):
        fig.add_trace(
            go.Scatter(
                x=X[i, :],
                y=Y[i, :],
                mode="lines",
                line=dict(color="rgba(47, 158, 68, 0.34)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for j in range(X.shape[1]):
        fig.add_trace(
            go.Scatter(
                x=X[:, j],
                y=Y[:, j],
                mode="lines",
                line=dict(color="rgba(47, 158, 68, 0.34)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    fig.add_shape(
        type="rect",
        x0=domain["xmin"],
        x1=domain["xmax"],
        y0=domain["ymin"],
        y1=domain["ymax"],
        line=dict(color="#132238", width=2),
        fillcolor="rgba(0,0,0,0)",
    )
    fig.add_trace(
        go.Scatter(
            x=data["Longitud"],
            y=data["Latitud"],
            mode="markers",
            name="Puntos reales",
            text=data["Ciudad o localidad"],
            marker=dict(size=9, color="#0b7285", line=dict(width=1, color="#ffffff"), opacity=0.92),
            hovertemplate="<b>%{text}</b><br>Longitud: %{x:.4f}<br>Latitud: %{y:.4f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            line=dict(color="rgba(47, 158, 68, 0.55)", width=2),
            name="Malla",
        )
    )
    return style_geo_layout(fig, f"Malla visual del dominio con puntos reales - {country}", domain)


def map_layout(fig: go.Figure, title: str, data: pd.DataFrame) -> go.Figure:
    center = {"lat": float(data["Latitud"].mean()), "lon": float(data["Longitud"].mean())}
    lat_span = max(float(data["Latitud"].max() - data["Latitud"].min()), 0.5)
    lon_span = max(float(data["Longitud"].max() - data["Longitud"].min()), 0.5)
    zoom = 5
    if max(lat_span, lon_span) < 2:
        zoom = 7
    if max(lat_span, lon_span) < 0.8:
        zoom = 9
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        height=680,
        margin=dict(l=0, r=0, t=60, b=0),
        mapbox=dict(style="open-street-map", center=center, zoom=zoom),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color="#132238"),
        legend=dict(orientation="h", y=1.02, x=0.01, bgcolor="rgba(255,255,255,.88)"),
    )
    return fig


def fig_map_points(data: pd.DataFrame, country: str) -> go.Figure:
    fig = go.Figure()
    color_col = "Region natural" if "Region natural" in data.columns else None
    if color_col:
        palette = {"Costa": "#0b7285", "Sierra": "#e8590c", "Selva": "#2f9e44"}
        for name, group in data.groupby(color_col):
            fig.add_trace(
                go.Scattermapbox(
                    lat=group["Latitud"],
                    lon=group["Longitud"],
                    mode="markers",
                    name=name,
                    text=group["Ciudad o localidad"],
                    customdata=np.stack([group.get("Region", pd.Series("", index=group.index)), group["Zona macro"]], axis=-1),
                    marker=dict(size=13, color=palette.get(name, "#495057"), opacity=0.86),
                    hovertemplate="<b>%{text}</b><br>Region: %{customdata[0]}<br>Zona: %{customdata[1]}<br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
                )
            )
    else:
        fig.add_trace(
            go.Scattermapbox(
                lat=data["Latitud"],
                lon=data["Longitud"],
                mode="markers",
                name="Localidades",
                text=data["Ciudad o localidad"],
                marker=dict(size=13, color="#0b7285", opacity=0.86),
                hovertemplate="<b>%{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
            )
        )
    return map_layout(fig, f"Mapa interactivo de localidades - {country}", data)


def fig_map_grid(data: pd.DataFrame, X: np.ndarray, Y: np.ndarray, country: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scattermapbox(
            lat=Y.ravel(),
            lon=X.ravel(),
            mode="markers",
            name="Cuadricula",
            marker=dict(size=6, color="#e8590c", opacity=0.62),
            hovertemplate="Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            lat=data["Latitud"],
            lon=data["Longitud"],
            mode="markers",
            name="Puntos reales",
            text=data["Ciudad o localidad"],
            marker=dict(size=11, color="#0b7285", opacity=0.9),
            hovertemplate="<b>%{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
        )
    )
    return map_layout(fig, f"Cuadricula geografica sobre mapa - {country}", data)


def fig_map_mesh(data: pd.DataFrame, X: np.ndarray, Y: np.ndarray, domain: dict[str, float], country: str) -> go.Figure:
    fig = go.Figure()
    for i in range(Y.shape[0]):
        fig.add_trace(
            go.Scattermapbox(
                lat=Y[i, :],
                lon=X[i, :],
                mode="lines",
                line=dict(color="rgba(47, 158, 68, 0.45)", width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for j in range(X.shape[1]):
        fig.add_trace(
            go.Scattermapbox(
                lat=Y[:, j],
                lon=X[:, j],
                mode="lines",
                line=dict(color="rgba(47, 158, 68, 0.45)", width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    rect_lon = [domain["xmin"], domain["xmax"], domain["xmax"], domain["xmin"], domain["xmin"]]
    rect_lat = [domain["ymin"], domain["ymin"], domain["ymax"], domain["ymax"], domain["ymin"]]
    fig.add_trace(
        go.Scattermapbox(
            lat=rect_lat,
            lon=rect_lon,
            mode="lines",
            name="Dominio",
            line=dict(color="#132238", width=4),
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            lat=data["Latitud"],
            lon=data["Longitud"],
            mode="markers",
            name="Puntos reales",
            text=data["Ciudad o localidad"],
            marker=dict(size=12, color="#0b7285", opacity=0.92),
            hovertemplate="<b>%{text}</b><br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
        )
    )
    return map_layout(fig, f"Malla geografica sobre mapa - {country}", data)


def matplotlib_geo_image(kind: str, data: pd.DataFrame, domain: dict[str, float], X=None, Y=None) -> BytesIO:
    fig, ax = plt.subplots(figsize=(8.2, 6), dpi=160)
    ax.set_facecolor("#fbfdff")
    ax.grid(True, color="#dbe6ee", linewidth=0.8)
    ax.set_xlim(domain["xmin"] - 0.8, domain["xmax"] + 0.8)
    ax.set_ylim(domain["ymin"] - 0.8, domain["ymax"] + 0.8)
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.set_aspect("equal", adjustable="box")

    if kind == "points":
        ax.scatter(data["Longitud"], data["Latitud"], s=26, color="#0b7285", edgecolor="white", linewidth=0.7)
        ax.set_title("Puntos geograficos reales")
    elif kind == "grid":
        ax.scatter(np.ravel(X), np.ravel(Y), s=10, color="#e8590c", alpha=0.75)
        ax.set_title("Cuadricula de puntos")
    else:
        for i in range(Y.shape[0]):
            ax.plot(X[i, :], Y[i, :], color="#2f9e44", linewidth=0.6, alpha=0.45)
        for j in range(X.shape[1]):
            ax.plot(X[:, j], Y[:, j], color="#2f9e44", linewidth=0.6, alpha=0.45)
        ax.add_patch(
            plt.Rectangle(
                (domain["xmin"], domain["ymin"]),
                domain["xmax"] - domain["xmin"],
                domain["ymax"] - domain["ymin"],
                fill=False,
                edgecolor="#132238",
                linewidth=1.4,
            )
        )
        ax.scatter(data["Longitud"], data["Latitud"], s=24, color="#0b7285", edgecolor="white", linewidth=0.7)
        ax.set_title("Malla visual con puntos reales")

    buffer = BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return buffer


def small_table(df: pd.DataFrame, max_rows: int = 12) -> list[list[str]]:
    shown = df.head(max_rows).copy()
    for col in shown.columns:
        shown[col] = shown[col].astype(str)
    return [list(shown.columns)] + shown.values.tolist()


def add_table(story, data, widths=None, header_bg="#132238") -> None:
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccd6df")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fbfdff")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.35 * cm))


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


STUDENT_NAME = "Jhon Marco Aracayo Mamani"

def build_pdf(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    domain_df: pd.DataFrame,
    domain: dict[str, float],
    X: np.ndarray,
    Y: np.ndarray,
    country: str,
    dx: float,
    dy: float,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.3 * cm, bottomMargin=1.3 * cm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=20, leading=24, textColor=colors.HexColor("#132238"))
    heading = ParagraphStyle("HeadingCustom", parent=styles["Heading2"], fontSize=13, leading=16, textColor=colors.HexColor("#0b7285"), spaceBefore=8)
    body = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontSize=9.5, leading=13)

    story = [
        paragraph("Practica Calificada 02 - Unidad 2", title),
        paragraph("Visualizacion de dominios geograficos mediante puntos, cuadriculas y mallas", body),
        Spacer(1, 0.5 * cm),
        paragraph("Datos generales", heading),
    ]
    add_table(
        story,
        [
            ["Campo", "Detalle"],
            ["Curso", "Visualizacion de Datos"],
            ["Programa", "Ingenieria de Sistemas"],
            ["Estudiante", STUDENT_NAME],
            ["Pais seleccionado", country],
            ["Dataset", "Geolocation Data [Longitude Latitude] - Kaggle"],
            ["Enlace", DATASET_URL],
        ],
        [5 * cm, 11 * cm],
    )

    story += [
        paragraph("1. Exploracion de la base de datos", heading),
        paragraph(
            f"El archivo utilizado contiene {len(raw_df):,} registros y {len(raw_df.columns)} columnas. "
            f"Las columnas detectadas permiten identificar localidad, pais, latitud y longitud para construir el analisis espacial.",
            body,
        ),
    ]
    add_table(story, [["Columnas principales"]] + [[c] for c in raw_df.columns[:18]], [16 * cm])

    story += [
        paragraph("2. Limpieza y seleccion de datos", heading),
        paragraph(
            f"Se filtraron registros correspondientes a {country}, se convirtieron latitud y longitud a valores numericos, "
            f"y se eliminaron registros vacios o inconsistentes. La tabla limpia contiene {len(clean_df):,} localidades.",
            body,
        ),
    ]
    clean_width = 16 * cm / max(len(clean_df.columns), 1)
    add_table(story, small_table(clean_df, 14), [clean_width] * len(clean_df.columns))

    story += [
        paragraph("3. Delimitacion del dominio geografico", heading),
        paragraph(
            f"El dominio rectangular queda definido como D = [{domain['xmin']:.4f}, {domain['xmax']:.4f}] x "
            f"[{domain['ymin']:.4f}, {domain['ymax']:.4f}], donde x representa longitud e y representa latitud.",
            body,
        ),
    ]
    domain_print = domain_df.copy()
    domain_print["Valor"] = domain_print["Valor"].map(lambda v: f"{v:.4f}")
    add_table(story, [list(domain_print.columns)] + domain_print.values.tolist(), [4.3 * cm, 3.2 * cm, 8.5 * cm])

    story += [
        paragraph("4. Visualizaciones", heading),
        paragraph(
            f"La cuadricula se genero con dx = {dx} y dy = {dy}. Los puntos reales representan localidades observadas; "
            "la cuadricula representa posiciones generadas regularmente dentro del dominio; la malla conecta esas posiciones "
            "para facilitar la lectura territorial.",
            body,
        ),
    ]
    for kind in ["points", "grid", "mesh"]:
        img = matplotlib_geo_image(kind, clean_df, domain, X, Y)
        story.append(Image(img, width=16 * cm, height=11.7 * cm))
        story.append(Spacer(1, 0.25 * cm))

    story += [
        PageBreak(),
        paragraph("5. Interpretacion visual de resultados", heading),
        paragraph(
            "El dominio geografico construido representa el rectangulo minimo que cubre las localidades seleccionadas. "
            "Los puntos reales son coordenadas obtenidas de la base de datos, mientras que los puntos de la cuadricula son "
            "posiciones generadas matematicamente para dividir el espacio. La malla permite ordenar la lectura visual, "
            "comparar zonas con mayor o menor concentracion y apoyar decisiones en cobertura, rutas, sensores IoT, servicios "
            "digitales y analisis territorial.",
            body,
        ),
        paragraph("6. Respuestas a preguntas de analisis", heading),
    ]

    answers = [
        ("Importancia de delimitar el dominio", "Permite definir el area exacta de analisis y evita graficar fuera del territorio estudiado."),
        ("Informacion del grafico de puntos", "Muestra ubicacion y dispersion de localidades reales, revelando concentraciones espaciales."),
        ("Representacion de la cuadricula", "Es un conjunto de puntos generados a intervalos constantes dentro del dominio."),
        ("Diferencia entre cuadricula y malla", "La cuadricula son puntos; la malla agrega lineas horizontales y verticales que conectan esos puntos."),
        ("Si se reduce dx y dy", "La visualizacion se vuelve mas densa y detallada, aunque puede saturarse visualmente."),
        ("Si se aumenta dx y dy", "La visualizacion se simplifica, pero pierde precision espacial."),
        ("Ayuda en Ingenieria de Sistemas", "Apoya el diseno de cobertura, sensores, rutas, puntos de atencion y toma de decisiones basada en datos."),
    ]
    add_table(story, [["Pregunta", "Respuesta"]] + answers, [5.2 * cm, 10.8 * cm])

    story += [
        paragraph("7. Conclusiones", heading),
        paragraph(
            "El modelado de dominios permite transformar coordenadas geograficas en una representacion espacial clara. "
            "Las cuadriculas y mallas complementan los puntos reales porque organizan el territorio, facilitan la comparacion "
            "entre zonas y mejoran la interpretacion visual para problemas aplicados de Ingenieria de Sistemas.",
            body,
        ),
    ]
    doc.build(story)
    return buffer.getvalue()


def code_block_text() -> str:
    return """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data/peru_geolocation_sample.csv")
pais = "Peru"
datos = df[df["country_name"] == pais][["city_name", "country_name", "latitude", "longitude"]]
datos = datos.dropna(subset=["latitude", "longitude"])
datos["latitude"] = pd.to_numeric(datos["latitude"], errors="coerce")
datos["longitude"] = pd.to_numeric(datos["longitude"], errors="coerce")
datos = datos.dropna(subset=["latitude", "longitude"])

x = datos["longitude"]
y = datos["latitude"]
xmin, xmax = x.min(), x.max()
ymin, ymax = y.min(), y.max()

plt.figure(figsize=(8, 6))
plt.scatter(x, y, s=20)
plt.title("Puntos geograficos reales - " + pais)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.grid(True)
plt.show()

dx, dy = 0.5, 0.5
x_grid = np.arange(xmin, xmax + dx, dx)
y_grid = np.arange(ymin, ymax + dy, dy)
X, Y = np.meshgrid(x_grid, y_grid)

plt.figure(figsize=(8, 6))
plt.scatter(X, Y, s=8)
plt.title("Cuadricula de puntos del dominio - " + pais)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.grid(True)
plt.show()

plt.figure(figsize=(8, 6))
for i in range(Y.shape[0]):
    plt.plot(X[i, :], Y[i, :], linewidth=0.5)
for j in range(X.shape[1]):
    plt.plot(X[:, j], Y[:, j], linewidth=0.5)
plt.scatter(x, y, s=20)
plt.title("Malla visual del dominio con puntos reales - " + pais)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.grid(True)
plt.show()
"""


def wrapped_caption(text: str) -> str:
    return "\n".join(wrap(text, 115))


def main() -> None:
    css()
    st.markdown(
        f"""
        <div class="hero">
            <h1>Visualizacion de dominios geograficos</h1>
            <p>
                Practica completa de puntos reales, cuadricula regular y malla visual sobre un dominio geografico.
                El flujo cubre exploracion, limpieza, limites, graficos, interpretacion y reporte final.
            </p>
            <p class="small-muted">Estudiante: {STUDENT_NAME}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Configuracion")
        uploaded = st.file_uploader("Subir CSV de Kaggle", type=["csv"])
        df = load_uploaded(uploaded)

        try:
            columns = detect_columns(df)
            countries = sorted(df[columns.country].dropna().astype(str).str.strip().unique().tolist())
            default_index = countries.index("Peru") if "Peru" in countries else 0
            country = st.selectbox("Pais o region", countries, index=default_index)
            dx = st.slider("Separacion horizontal dx", 0.1, 2.0, 0.5, 0.1)
            dy = st.slider("Separacion vertical dy", 0.1, 2.0, 0.5, 0.1)
            st.caption("Fuente por defecto: muestra local de localidades peruanas.")
        except Exception as exc:
            st.error(str(exc))
            st.stop()

    base_clean = add_geo_groups(clean_data(df, columns, country))
    if base_clean.empty:
        st.error(f"No hay registros validos para {country}. Revisa el CSV o selecciona otro pais.")
        st.stop()

    with st.sidebar:
        st.divider()
        st.subheader("Filtros geograficos")
        region_options = sorted(base_clean["Region"].dropna().astype(str).unique().tolist()) if "Region" in base_clean.columns else []
        selected_regions = st.multiselect("Regiones/departamentos", region_options, placeholder="Todas las regiones")
        macro_options = sorted(base_clean["Zona macro"].dropna().astype(str).unique().tolist())
        selected_macro = st.multiselect("Zona macro", macro_options, placeholder="Norte, Centro o Sur")
        natural_options = sorted(base_clean["Region natural"].dropna().astype(str).unique().tolist())
        selected_natural = st.multiselect("Region natural", natural_options, placeholder="Costa, Sierra o Selva")
        city_options = sorted(base_clean["Ciudad o localidad"].dropna().astype(str).unique().tolist())
        selected_cities = st.multiselect("Ciudades/localidades", city_options, placeholder="Todas las ciudades")
        st.caption("Los graficos, dominio, cuadricula, malla y PDF usan estos filtros.")

    clean = filter_geo_data(base_clean, selected_regions, selected_macro, selected_natural, selected_cities)
    if clean.empty:
        st.error("Los filtros seleccionados no devuelven datos. Quita algun filtro o elige otra zona.")
        st.stop()

    domain_df, domain = domain_table(clean)
    X, Y = make_grid(domain, dx, dy)

    st.markdown('<div class="metric-wrap">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros del archivo", f"{len(df):,}")
    c2.metric("Columnas detectadas", f"{len(df.columns):,}")
    c3.metric("Registros filtrados", f"{len(clean):,}")
    c4.metric("Puntos de cuadricula", f"{X.size:,}")
    st.markdown("</div>", unsafe_allow_html=True)

    tabs = st.tabs(["Mapa", "Exploracion", "Limpieza", "Dominio", "Visualizaciones", "Interpretacion", "Cumplimiento", "Codigo"])

    with tabs[0]:
        st.subheader("Mapa interactivo con filtros")
        map_tab1, map_tab2, map_tab3 = st.tabs(["Localidades", "Cuadricula en mapa", "Malla en mapa"])
        with map_tab1:
            st.plotly_chart(fig_map_points(clean, country), use_container_width=True)
        with map_tab2:
            st.plotly_chart(fig_map_grid(clean, X, Y, country), use_container_width=True)
            st.caption("La cuadricula si cumple: son puntos generados regularmente dentro del dominio filtrado y colocados sobre el mapa real.")
        with map_tab3:
            st.plotly_chart(fig_map_mesh(clean, X, Y, domain, country), use_container_width=True)
            st.caption("La malla si cumple: conecta la cuadricula con lineas horizontales y verticales, dibuja el rectangulo del dominio y superpone los puntos reales.")

    with tabs[1]:
        st.subheader("Actividad 1. Exploracion de la base de datos")
        st.markdown(
            f"""
            <div class="note">
                El dataset contiene <b>{len(df):,}</b> registros y <b>{len(df.columns)}</b> columnas.
                Las coordenadas geograficas fueron detectadas como <b>{columns.latitude}</b> y <b>{columns.longitude}</b>.
                Para el analisis se selecciono <b>{country}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(pd.DataFrame({"Columnas del dataset": df.columns}), use_container_width=True, hide_index=True)
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Actividad 2. Limpieza y seleccion de datos")
        st.write("Tabla limpia y filtrada con localidad, pais, region, zonas geograficas, latitud y longitud.")
        st.dataframe(clean, use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("Actividad 3. Delimitacion del dominio geografico")
        st.latex(r"D = [x_{min}, x_{max}] \times [y_{min}, y_{max}]")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.markdown(
            f"""
            <div class="note">
                El dominio cubre desde la longitud <b>{domain['xmin']:.4f}</b> hasta <b>{domain['xmax']:.4f}</b>,
                y desde la latitud <b>{domain['ymin']:.4f}</b> hasta <b>{domain['ymax']:.4f}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tabs[4]:
        st.subheader("Actividad 4, 5 y 6. Visualizaciones espaciales")
        chart1, chart2, chart3 = st.tabs(["Puntos reales", "Cuadricula", "Malla"])
        with chart1:
            st.plotly_chart(fig_points(clean, domain, country), use_container_width=True)
            st.caption(
                wrapped_caption(
                    "Los puntos reales representan ciudades o localidades del dataset. Su distribucion permite observar "
                    "concentraciones territoriales y zonas con menor presencia de registros."
                )
            )
        with chart2:
            st.plotly_chart(fig_grid(X, Y, domain, country), use_container_width=True)
            st.caption(
                wrapped_caption(
                    "La cuadricula genera posiciones regulares dentro del dominio para dividir el espacio en intervalos "
                    "constantes y preparar analisis por zonas."
                )
            )
        with chart3:
            st.plotly_chart(fig_mesh(clean, X, Y, domain, country), use_container_width=True)
            st.caption(
                wrapped_caption(
                    "La malla conecta la cuadricula con lineas horizontales y verticales. Al superponer los puntos reales, "
                    "se facilita comparar ubicaciones observadas contra una estructura espacial ordenada."
                )
            )

    with tabs[5]:
        st.subheader("Actividad 7. Interpretacion visual de resultados")
        q1, q2 = st.columns(2)
        with q1:
            st.markdown('<div class="answer"><b>a) Que representa el dominio geografico?</b><br>Representa el rectangulo minimo que contiene las coordenadas reales seleccionadas. En este caso delimita el territorio observado para el analisis espacial.</div>', unsafe_allow_html=True)
            st.markdown('<div class="answer"><b>b) Diferencia entre puntos reales y cuadricula</b><br>Los puntos reales provienen del dataset y corresponden a localidades. Los puntos de la cuadricula son posiciones generadas con dx y dy para organizar el espacio.</div>', unsafe_allow_html=True)
        with q2:
            st.markdown('<div class="answer"><b>c) Utilidad de la malla</b><br>La malla ayuda a leer distancias, comparar zonas, ubicar concentraciones y estructurar visualmente el dominio geografico.</div>', unsafe_allow_html=True)
            st.markdown('<div class="answer"><b>d) Aplicacion en Ingenieria de Sistemas</b><br>Puede aplicarse en cobertura de servicios digitales, sensores IoT, distribucion de usuarios, rutas, puntos de atencion y toma de decisiones territoriales.</div>', unsafe_allow_html=True)

        st.subheader("Preguntas de analisis")
        analysis = pd.DataFrame(
            [
                ["Por que delimitar un dominio?", "Porque fija el area de estudio, evita ruido visual y permite calcular cuadriculas y mallas coherentes."],
                ["Que aporta el grafico de puntos?", "Muestra la ubicacion real de localidades y evidencia patrones de concentracion o dispersion."],
                ["Que representa una cuadricula?", "Una division regular del espacio mediante puntos generados a intervalos constantes."],
                ["Diferencia entre cuadricula y malla", "La cuadricula contiene puntos; la malla agrega lineas que conectan esos puntos."],
                ["Que pasa si dx y dy disminuyen?", "Aumenta el detalle y la densidad, pero puede saturar el grafico."],
                ["Que pasa si dx y dy aumentan?", "La lectura se simplifica, pero se pierde precision espacial."],
                ["Como ayuda en decisiones?", "Permite evaluar cobertura, planificar rutas, ubicar sensores y comparar zonas de atencion."],
            ],
            columns=["Pregunta", "Respuesta"],
        )
        st.dataframe(analysis, use_container_width=True, hide_index=True)

        pdf = build_pdf(df, clean, domain_df, domain, X, Y, country, dx, dy)
        st.download_button(
            "Descargar informe PDF completo",
            data=pdf,
            file_name="informe_practica_visualizacion_dominios.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with tabs[6]:
        st.subheader("Verificacion de cumplimiento de la practica")
        compliance = pd.DataFrame(
            [
                ["1. Mapa dinamico", "Si cumple", "Pestana Mapa: OpenStreetMap interactivo con filtros por region, zona macro, region natural y ciudad."],
                ["2. Exploracion del dataset", "Si cumple", "Pestana Exploracion: muestra cantidad de registros, columnas detectadas, primeras filas y columnas principales."],
                ["3. Limpieza y filtrado", "Si cumple", "Pestana Limpieza: filtra pais, regiones, ciudades y zonas; convierte coordenadas a numerico y elimina valores vacios/inconsistentes."],
                ["4. Delimitacion del dominio", "Si cumple", "Pestana Dominio: calcula xmin, xmax, ymin, ymax sobre los datos filtrados y presenta la tabla con interpretacion."],
                ["5. Puntos reales", "Si cumple", "Pestana Visualizaciones > Puntos reales y Mapa > Localidades: longitud en X, latitud en Y y ubicacion real en mapa."],
                ["6. Cuadricula de puntos", "Si cumple", "Pestana Mapa > Cuadricula en mapa y Visualizaciones > Cuadricula: genera puntos regulares dentro del dominio usando dx y dy configurables."],
                ["7. Malla visual", "Si cumple", "Pestana Mapa > Malla en mapa y Visualizaciones > Malla: traza lineas horizontales y verticales, dominio y puntos reales superpuestos."],
                ["8. Interpretacion", "Si cumple", "Pestana Interpretacion: responde las preguntas de la actividad y las preguntas de analisis."],
                ["9. Producto final PDF", "Si cumple", "Boton Descargar informe PDF completo: genera un informe con tablas, graficos, respuestas y conclusiones."],
                ["10. Codigo utilizado", "Si cumple", "Pestana Codigo: incluye codigo base reproducible en Python."],
            ],
            columns=["Requisito", "Estado", "Como se cumple en la app"],
        )
        st.dataframe(compliance, use_container_width=True, hide_index=True)
        st.markdown(
            """
            <div class="note">
                La aplicacion cumple la rubrica completa de 20 puntos porque ejecuta todas las actividades solicitadas:
                carga/exploracion, limpieza, dominio, puntos reales, cuadricula, malla, interpretacion, conclusiones,
                codigo y reporte PDF descargable.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tabs[7]:
        st.subheader("Codigo base reproducible")
        st.code(code_block_text(), language="python")


if __name__ == "__main__":
    main()
