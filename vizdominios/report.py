"""Generador del informe PDF (producto final de la practica).

Construye con ReportLab un documento con caratula institucional, indice,
las siete actividades documentadas, los tres graficos obligatorios, analisis
complementario, respuestas a las preguntas, conclusiones, verificacion de la
rubrica y anexo de codigo.

Se usa desde ``main.py`` (``python main.py`` genera el PDF) y desde la app
Streamlit (boton de descarga), siempre a partir del mismo ``AnalysisResult``.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import config as cfg
from . import content, figures
from .analysis import coordinate_summary, real_vs_generated, resolution_sensitivity
from .dataio import column_profile, dataset_overview
from .pipeline import AnalysisResult

PAGE_WIDTH = A4[0]
CONTENT_WIDTH = PAGE_WIDTH - 3.0 * cm  # margenes de 1.5 cm por lado
INK = colors.HexColor(cfg.PALETTE["ink"])
ACCENT = colors.HexColor(cfg.PALETTE["real"])
MUTED = colors.HexColor(cfg.PALETTE["muted"])
LINE = colors.HexColor("#ccd6df")
SOFT_BG = colors.HexColor(cfg.PALETTE["surface"])


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontSize=22, leading=26, textColor=INK
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub",
            parent=base["Normal"],
            fontSize=12.5,
            leading=17,
            alignment=TA_CENTER,
            textColor=ACCENT,
        ),
        "cover_line": ParagraphStyle(
            "CoverLine",
            parent=base["Normal"],
            fontSize=10.5,
            leading=15,
            alignment=TA_CENTER,
            textColor=INK,
        ),
        "cover_small": ParagraphStyle(
            "CoverSmall",
            parent=base["Normal"],
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=MUTED,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=14,
            leading=18,
            textColor=ACCENT,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=11.5,
            leading=15,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontSize=9.6,
            leading=13.6,
            alignment=TA_JUSTIFY,
            textColor=INK,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontSize=8.4,
            leading=11,
            alignment=TA_CENTER,
            textColor=MUTED,
        ),
        "cell": ParagraphStyle(
            "Cell", parent=base["Normal"], fontSize=8.2, leading=10.6, textColor=INK
        ),
        "cell_head": ParagraphStyle(
            "CellHead",
            parent=base["Normal"],
            fontSize=8.4,
            leading=11,
            textColor=colors.white,
        ),
        "code": ParagraphStyle(
            "Code", parent=base["Code"], fontSize=6.6, leading=8.1, textColor=INK
        ),
    }


# ---------------------------------------------------------------------------
# Componentes reutilizables
# ---------------------------------------------------------------------------
def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text).replace("\n", "<br/>"), style)


def _table(
    rows: list[list], widths: list[float], styles: dict, align_right: list[int] | None = None
) -> Table:
    """Tabla con encabezado oscuro, celdas envolventes y cebra suave."""
    body = [[_p(cell, styles["cell_head"]) for cell in rows[0]]]
    for row in rows[1:]:
        body.append([_p(cell, styles["cell"]) for cell in row])

    table = Table(body, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT_BG]),
    ]
    for col in align_right or []:
        commands.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))
    table.setStyle(TableStyle(commands))
    return table


def _df_table(
    df: pd.DataFrame,
    styles: dict,
    max_rows: int | None = None,
    widths: list[float] | None = None,
    decimals: int = 4,
) -> Table:
    """Convierte un DataFrame en tabla del informe."""
    shown = df if max_rows is None else df.head(max_rows)
    formatted = shown.copy()
    for col in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[col]):
            formatted[col] = formatted[col].map(lambda v: f"{v:.{decimals}f}")
        formatted[col] = formatted[col].astype(str)
    rows = [list(formatted.columns)] + formatted.values.tolist()
    if widths is None:
        widths = [CONTENT_WIDTH / len(formatted.columns)] * len(formatted.columns)
    return _table(rows, widths, styles)


def _figure(
    fig,
    styles: dict,
    caption: str,
    width: float = CONTENT_WIDTH,
    aspect: float = 6.2 / 8.6,
) -> list:
    """Inserta una figura Matplotlib con su pie de figura.

    ``aspect`` es la razon alto/ancho de la figura original, para que la imagen
    no salga deformada en el PDF.
    """
    buffer = figures.render_png(fig)
    height = width * aspect
    return [
        Image(buffer, width=width, height=height),
        Spacer(1, 0.12 * cm),
        _p(caption, styles["caption"]),
        Spacer(1, 0.45 * cm),
    ]


def _page_decorations(canvas, doc) -> None:
    """Encabezado y pie con numeracion en todas las paginas menos la caratula."""
    canvas.saveState()
    if doc.page > 1:
        canvas.setFont("Helvetica", 7.4)
        canvas.setFillColor(MUTED)
        canvas.drawString(1.5 * cm, A4[1] - 1.0 * cm, f"{cfg.COURSE} - {cfg.PRACTICE_TITLE}")
        canvas.drawRightString(
            A4[0] - 1.5 * cm, A4[1] - 1.0 * cm, cfg.STUDENT_NAME
        )
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.4)
        canvas.line(1.5 * cm, A4[1] - 1.15 * cm, A4[0] - 1.5 * cm, A4[1] - 1.15 * cm)
        canvas.line(1.5 * cm, 1.15 * cm, A4[0] - 1.5 * cm, 1.15 * cm)
        canvas.drawString(1.5 * cm, 0.85 * cm, cfg.PROGRAM)
        canvas.drawRightString(A4[0] - 1.5 * cm, 0.85 * cm, f"Pagina {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Caratula
# ---------------------------------------------------------------------------
def _logo(path: Path, height: float = 2.5 * cm) -> Image | str:
    """Logo escalado a una altura fija respetando su proporcion original."""
    if not path.exists():
        return ""
    natural_width, natural_height = ImageReader(str(path)).getSize()
    ratio = natural_width / natural_height if natural_height else 1.0
    return Image(str(path), width=height * ratio, height=height)


def _cover(styles: dict) -> list:
    logos: list = []
    cells = [_logo(cfg.LOGO_UNAP), _logo(cfg.LOGO_EPISI)]
    if any(not isinstance(c, str) for c in cells):
        logo_table = Table([cells], colWidths=[CONTENT_WIDTH / 2] * 2)
        logo_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        logos = [logo_table, Spacer(1, 0.5 * cm)]

    return [
        *logos,
        _p(cfg.UNIVERSITY.upper(), styles["cover_line"]),
        _p(cfg.FACULTY, styles["cover_small"]),
        _p(cfg.PROGRAM, styles["cover_small"]),
        Spacer(1, 1.9 * cm),
        _p(cfg.PRACTICE_TITLE, styles["cover_title"]),
        Spacer(1, 0.25 * cm),
        _p(cfg.PRACTICE_SUBTITLE, styles["cover_sub"]),
        Spacer(1, 1.6 * cm),
        _p("INFORME DE RESULTADOS", styles["cover_line"]),
        Spacer(1, 1.9 * cm),
    ]


def _general_data(result: AnalysisResult, styles: dict) -> list:
    rows = [
        ["Campo", "Detalle"],
        ["Estudiante", cfg.STUDENT_NAME],
        ["Curso", cfg.COURSE],
        ["Programa de estudios", "Ingenieria de Sistemas"],
        ["Semestre", cfg.SEMESTER],
        ["Unidad tematica", cfg.UNIT],
        ["Tema", "Modelado de dominios, mallas y cuadriculas de puntos"],
        ["Tipo de actividad", f"Practica calificada individual ({cfg.TOTAL_POINTS} puntos)"],
        ["Dataset", f"{cfg.DATASET_NAME} ({cfg.DATASET_SOURCE})"],
        ["Enlace del dataset", cfg.DATASET_URL],
        ["Archivo procesado", result.source_label],
        ["Pais seleccionado", result.country],
        ["Repositorio del codigo", cfg.REPO_URL],
        ["Fecha de emision", date.today().strftime("%d/%m/%Y")],
    ]
    return [_table(rows, [5.0 * cm, CONTENT_WIDTH - 5.0 * cm], styles)]


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------
def _section_dataset(result: AnalysisResult, styles: dict) -> list:
    story = [
        _p("1. Descripcion del dataset utilizado", styles["h1"]),
        _p(content.dataset_description(result), styles["body"]),
        Spacer(1, 0.3 * cm),
        _p("2. Exploracion inicial (Actividad 1)", styles["h1"]),
        _df_table(dataset_overview(result.raw, result.columns), styles,
                  widths=[6.2 * cm, CONTENT_WIDTH - 6.2 * cm]),
        Spacer(1, 0.35 * cm),
        _p("2.1 Perfil de las columnas principales", styles["h2"]),
        _df_table(column_profile(result.raw), styles, max_rows=12),
        Spacer(1, 0.2 * cm),
        _p("2.2 Rol de cada columna en la practica", styles["h2"]),
        _df_table(result.columns.as_table(), styles,
                  widths=[4.0 * cm, 4.5 * cm, CONTENT_WIDTH - 8.5 * cm]),
        Spacer(1, 0.25 * cm),
        _p("2.3 Primeras filas del archivo original", styles["h2"]),
        _df_table(result.raw.head(8), styles),
    ]
    return story


def _section_cleaning(result: AnalysisResult, styles: dict) -> list:
    clean = result.clean
    mostrar = clean[[c for c in cfg.CLEAN_COLUMNS if c in clean.columns]]
    return [
        PageBreak(),
        _p("3. Limpieza y seleccion de datos (Actividad 2)", styles["h1"]),
        _p(
            f"Se filtraron los registros de {result.country} y se depuraron las "
            "coordenadas en cinco pasos verificables: filtro de pais, conversion a "
            "valores numericos, eliminacion de nulos, descarte de coordenadas fuera "
            "de rango geografico valido y eliminacion de duplicados de ciudad y "
            f"coordenada. El resultado es una tabla de {len(clean):,} localidades con "
            "las columnas minimas exigidas: Ciudad o localidad, Pais, Latitud y "
            "Longitud.",
            styles["body"],
        ),
        Spacer(1, 0.25 * cm),
        _p("3.1 Auditoria de la limpieza", styles["h2"]),
        _df_table(result.cleaning.as_table(), styles,
                  widths=[CONTENT_WIDTH - 3.5 * cm, 3.5 * cm]),
        Spacer(1, 0.2 * cm),
        _p("3.2 Tabla limpia con los datos geograficos", styles["h2"]),
        _df_table(mostrar, styles, max_rows=22),
        _p(
            f"Se muestran las primeras 22 de {len(clean):,} filas. La tabla completa "
            "se exporta a salidas/tabla_limpia.csv al ejecutar el proyecto.",
            styles["caption"],
        ),
        Spacer(1, 0.3 * cm),
        _p("3.3 Estadisticos descriptivos de las coordenadas", styles["h2"]),
        _df_table(coordinate_summary(clean), styles),
    ]


def _section_domain(result: AnalysisResult, styles: dict) -> list:
    domain = result.domain
    lon_c, lat_c = domain.center
    derived = pd.DataFrame(
        [
            ["Amplitud en longitud (xmax - xmin)", f"{domain.width:.4f} grados"],
            ["Amplitud en latitud (ymax - ymin)", f"{domain.height:.4f} grados"],
            ["Centro del dominio", f"lon {lon_c:.4f} / lat {lat_c:.4f}"],
            ["Area del rectangulo", f"{domain.area_deg2:.4f} grados cuadrados"],
            ["Area aproximada en km2", f"{domain.area_km2:,.0f} km2"],
        ],
        columns=["Metrica derivada", "Valor"],
    )
    return [
        PageBreak(),
        _p("4. Delimitacion del dominio geografico (Actividad 3)", styles["h1"]),
        _p(
            "A partir de las coordenadas filtradas se calcularon los valores minimos "
            "y maximos de longitud y latitud, con los que se define el dominio "
            f"rectangular <b>{domain.notation()}</b>, donde x es la longitud e y la "
            "latitud.",
            styles["body"],
        ),
        Spacer(1, 0.25 * cm),
        _df_table(domain.as_table(), styles,
                  widths=[5.0 * cm, 3.2 * cm, CONTENT_WIDTH - 8.2 * cm]),
        Spacer(1, 0.25 * cm),
        _p("4.1 Interpretacion del area representada", styles["h2"]),
        _df_table(derived, styles, widths=[7.5 * cm, CONTENT_WIDTH - 7.5 * cm]),
        Spacer(1, 0.2 * cm),
        _p(
            "El dominio representa el rectangulo minimo que contiene todas las "
            "localidades seleccionadas: su borde occidental corresponde al punto mas "
            "al oeste, el oriental al mas al este, el sur al de menor latitud y el "
            "norte al de mayor latitud. Es el marco de referencia sobre el que se "
            "construyen la cuadricula y la malla de las secciones siguientes.",
            styles["body"],
        ),
    ]


def _section_visualizations(result: AnalysisResult, styles: dict) -> list:
    grid = result.grid
    story = [
        PageBreak(),
        _p("5. Visualizacion de puntos geograficos reales (Actividad 4)", styles["h1"]),
    ]
    story += _figure(
        figures.fig_points(result.clean, result.domain, result.country),
        styles,
        "Figura 1. Dispersion de las coordenadas reales: longitud en el eje X, "
        "latitud en el eje Y, cuadricula de fondo y rectangulo del dominio.",
    )
    story += [
        _p("5.1 Interpretacion de la distribucion espacial", styles["h2"]),
        _p(content.distribution_comment(result), styles["body"]),
        PageBreak(),
        _p("6. Generacion de la cuadricula de puntos (Actividad 5)", styles["h1"]),
        _p(
            f"Con np.arange y np.meshgrid se genero una cuadricula regular dentro del "
            f"dominio, con separacion dx = {grid.dx} en longitud y dy = {grid.dy} en "
            f"latitud. El limite superior se extiende a xmax + dx y ymax + dy para "
            f"asegurar que los bordes del dominio queden cubiertos, ya que np.arange "
            f"excluye el extremo final.",
            styles["body"],
        ),
        Spacer(1, 0.2 * cm),
        _df_table(grid.as_table(), styles, widths=[7.5 * cm, CONTENT_WIDTH - 7.5 * cm]),
        Spacer(1, 0.3 * cm),
    ]
    story += _figure(
        figures.fig_grid(grid, result.country),
        styles,
        f"Figura 2. Cuadricula regular de {grid.size:,} puntos generados dentro del "
        f"dominio (dx = {grid.dx}, dy = {grid.dy}).",
    )
    story += [
        PageBreak(),
        _p("7. Construccion de la malla visual (Actividad 6)", styles["h1"]),
        _p(
            f"Uniendo los nodos de la cuadricula se trazaron {grid.ny} lineas "
            f"horizontales y {grid.nx} lineas verticales, se dibujo el rectangulo del "
            f"dominio y se superpusieron los {len(result.clean):,} puntos reales. La "
            f"malla resultante divide el dominio en {grid.cells:,} celdas comparables.",
            styles["body"],
        ),
        Spacer(1, 0.2 * cm),
    ]
    story += _figure(
        figures.fig_mesh(result.clean, grid, result.country),
        styles,
        "Figura 3. Malla visual con lineas horizontales y verticales, dominio "
        "rectangular y puntos reales superpuestos.",
    )
    return story


def _section_extra_analysis(result: AnalysisResult, styles: dict) -> list:
    occupancy = result.occupancy
    story = [
        PageBreak(),
        _p("8. Analisis complementario: densidad y resolucion", styles["h1"]),
        _p(
            "Esta seccion va mas alla de lo minimo exigido y usa la malla como "
            "instrumento de medida: se cuentan los puntos reales que caen en cada "
            "celda y se evalua como cambia la lectura al modificar dx y dy.",
            styles["body"],
        ),
        Spacer(1, 0.25 * cm),
        _p("8.1 Cobertura de la malla", styles["h2"]),
        _df_table(occupancy.as_table(), styles, widths=[8.0 * cm, CONTENT_WIDTH - 8.0 * cm]),
        Spacer(1, 0.25 * cm),
    ]
    story += _figure(
        figures.fig_density(result.clean, result.grid, result.country),
        styles,
        "Figura 4. Mapa de calor de localidades por celda. Las celdas sin color no "
        "contienen ninguna localidad registrada.",
    )
    if not occupancy.table.empty:
        story += [
            _p("8.2 Celdas con mayor concentracion", styles["h2"]),
            _df_table(occupancy.table, styles, max_rows=8),
            Spacer(1, 0.25 * cm),
        ]
    story += [
        PageBreak(),
        _p("8.3 Puntos reales frente a puntos generados", styles["h2"]),
        _df_table(
            real_vs_generated(result.clean, result.grid),
            styles,
            widths=[3.6 * cm, (CONTENT_WIDTH - 3.6 * cm) / 2, (CONTENT_WIDTH - 3.6 * cm) / 2],
        ),
        Spacer(1, 0.3 * cm),
        _p("8.4 Sensibilidad a los valores de dx y dy", styles["h2"]),
        _df_table(resolution_sensitivity(result.clean, result.domain), styles),
        Spacer(1, 0.25 * cm),
    ]
    story += _figure(
        figures.fig_resolution_panel(result.clean, result.domain),
        styles,
        "Figura 5. La misma malla con dx = dy igual a 0.25, 0.5, 1.0 y 2.0. Al reducir "
        "el paso aumenta el detalle y la saturacion visual; al aumentarlo se gana "
        "legibilidad y se pierde precision.",
        aspect=7.6 / 9.6,
    )
    return story


def _section_interpretation(result: AnalysisResult, styles: dict) -> list:
    story = [
        PageBreak(),
        _p("9. Interpretacion visual de resultados (Actividad 7)", styles["h1"]),
    ]
    for pregunta, respuesta in content.activity7_answers(result):
        story.append(
            KeepTogether(
                [
                    _p(pregunta, styles["h2"]),
                    _p(respuesta, styles["body"]),
                    Spacer(1, 0.18 * cm),
                ]
            )
        )
    story += [
        Spacer(1, 0.2 * cm),
        _p("9.1 Aplicaciones en Ingenieria de Sistemas", styles["h2"]),
        _table(
            [["Caso de aplicacion", "Como se usa el dominio y la malla"]]
            + [list(row) for row in content.systems_applications()],
            [5.2 * cm, CONTENT_WIDTH - 5.2 * cm],
            styles,
        ),
        PageBreak(),
        _p("10. Preguntas de analisis", styles["h1"]),
    ]
    for pregunta, respuesta in content.analysis_answers(result):
        story.append(
            KeepTogether(
                [
                    _p(f"<b>{pregunta}</b>", styles["body"]),
                    Spacer(1, 0.08 * cm),
                    _p(respuesta, styles["body"]),
                    Spacer(1, 0.22 * cm),
                ]
            )
        )
    return story


def _section_conclusions(result: AnalysisResult, styles: dict) -> list:
    story = [
        PageBreak(),
        _p("11. Conclusiones", styles["h1"]),
    ]
    for i, texto in enumerate(content.conclusions(result), start=1):
        story.append(_p(f"<b>{i}.</b> {texto}", styles["body"]))
        story.append(Spacer(1, 0.16 * cm))

    story += [
        Spacer(1, 0.3 * cm),
        _p("12. Verificacion de la rubrica de evaluacion", styles["h1"]),
        _p(
            f"La tabla siguiente relaciona cada criterio de la rubrica "
            f"({cfg.TOTAL_POINTS} puntos) con la evidencia concreta presentada en este "
            "informe y en el repositorio del proyecto.",
            styles["body"],
        ),
        Spacer(1, 0.2 * cm),
        _table(
            [["Criterio de evaluacion", "Pts", "Evidencia en este trabajo"]]
            + content.rubric_rows(result),
            [4.2 * cm, 1.1 * cm, CONTENT_WIDTH - 5.3 * cm],
            styles,
        ),
    ]
    return story


def _section_code(result: AnalysisResult, styles: dict) -> list:
    return [
        PageBreak(),
        _p("13. Anexo: codigo utilizado en Python", styles["h1"]),
        _p(
            "Version minima y autocontenida que reproduce las siete actividades con "
            "pandas, numpy y matplotlib. El proyecto completo (aplicacion Streamlit "
            "modular, tests y generador de este informe) esta disponible en "
            f"{cfg.REPO_URL}.",
            styles["body"],
        ),
        Spacer(1, 0.25 * cm),
        Preformatted(content.code_annex(result), styles["code"]),
    ]


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------
def build_report(result: AnalysisResult) -> bytes:
    """Construye el informe PDF completo y devuelve sus bytes."""
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"{cfg.PRACTICE_TITLE} - {cfg.PRACTICE_SUBTITLE}",
        author=cfg.STUDENT_NAME,
        subject=cfg.COURSE,
    )

    story: list = []
    story += _cover(styles)
    story += _general_data(result, styles)
    story += [
        PageBreak(),
        _p("Indice del informe", styles["h1"]),
        _table(
            [["Seccion", "Contenido"]] + [list(r) for r in content.report_index()],
            [2.4 * cm, CONTENT_WIDTH - 2.4 * cm],
            styles,
        ),
        Spacer(1, 0.4 * cm),
        _p("Resumen de resultados", styles["h1"]),
        _table(
            [["Indicador", "Valor"]] + [list(r) for r in content.numeric_highlights(result)],
            [8.0 * cm, CONTENT_WIDTH - 8.0 * cm],
            styles,
        ),
        Spacer(1, 0.35 * cm),
        _p("Trazabilidad de las actividades", styles["h1"]),
        _table(
            [["Actividad", "Resultado obtenido"]]
            + [[line[:12], line[13:]] for line in result.summary_lines()],
            [2.4 * cm, CONTENT_WIDTH - 2.4 * cm],
            styles,
        ),
    ]
    story += _section_dataset(result, styles)
    story += _section_cleaning(result, styles)
    story += _section_domain(result, styles)
    story += _section_visualizations(result, styles)
    story += _section_extra_analysis(result, styles)
    story += _section_interpretation(result, styles)
    story += _section_conclusions(result, styles)
    story += _section_code(result, styles)

    doc.build(story, onFirstPage=_page_decorations, onLaterPages=_page_decorations)
    return buffer.getvalue()


def save_report(result: AnalysisResult, path: Path | None = None) -> Path:
    """Genera el informe y lo guarda en disco."""
    target = path or (cfg.REPORT_DIR / cfg.REPORT_FILENAME)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(build_report(result))
    return target
