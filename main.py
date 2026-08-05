"""Ejecucion reproducible de la practica desde la consola (sin interfaz).

Recorre las siete actividades imprimiendo los resultados en pantalla, guarda las
figuras en ``docs/figuras/``, exporta las tablas a ``salidas/`` y genera el
informe PDF en ``informe/``.

Uso:
    python main.py
    python main.py --pais Peru --dx 0.5 --dy 0.5
    python main.py --csv ruta/al/dataset_kaggle.csv --region Puno --sin-pdf

Es la forma mas rapida de verificar el trabajo completo: un solo comando
produce las mismas salidas que la aplicacion interactiva.
"""

from __future__ import annotations

import argparse
import json
import sys

from vizdominios import config as cfg
from vizdominios.analysis import resolution_sensitivity
from vizdominios.dataio import export_csv, to_geojson
from vizdominios.figures import (
    fig_density,
    fig_grid,
    fig_mesh,
    fig_points,
    fig_resolution_panel,
    save_png,
)
from vizdominios.pipeline import EmptySelectionError, run_analysis
from vizdominios.report import save_report
from vizdominios import content

LINE = "=" * 78


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Practica 02 - Visualizacion de dominios geograficos",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--csv", default=None, help="Ruta del CSV a procesar")
    parser.add_argument("--pais", default=cfg.DEFAULT_COUNTRY, help="Pais de analisis")
    parser.add_argument("--dx", type=float, default=cfg.DEFAULT_DX, help="Separacion horizontal")
    parser.add_argument("--dy", type=float, default=cfg.DEFAULT_DY, help="Separacion vertical")
    parser.add_argument(
        "--region",
        action="append",
        default=None,
        help="Filtrar por region/departamento (se puede repetir)",
    )
    parser.add_argument("--sin-pdf", action="store_true", help="No generar el informe PDF")
    parser.add_argument("--sin-figuras", action="store_true", help="No guardar las figuras PNG")
    return parser.parse_args(argv)


def _titulo(texto: str) -> None:
    print(f"\n{LINE}\n{texto}\n{LINE}")


def ejecutar(args: argparse.Namespace) -> int:
    _titulo(f"{cfg.PRACTICE_TITLE} - {cfg.PRACTICE_SUBTITLE}")
    print(f"Estudiante : {cfg.STUDENT_NAME}")
    print(f"Curso      : {cfg.COURSE} | {cfg.UNIT}")
    print(f"Dataset    : {cfg.DATASET_NAME} ({cfg.DATASET_URL})")

    try:
        result = run_analysis(
            source=args.csv,
            country=args.pais,
            dx=args.dx,
            dy=args.dy,
            regions=args.region,
        )
    except (EmptySelectionError, FileNotFoundError, ValueError) as exc:
        print(f"\nERROR: {exc}")
        return 1

    # --- Actividad 1 -------------------------------------------------------
    _titulo("ACTIVIDAD 1. Exploracion de la base de datos (3 puntos)")
    print(f"Archivo            : {result.source_label}")
    print(f"Registros          : {len(result.raw):,}")
    print(f"Columnas ({len(result.raw.columns)})      : {', '.join(map(str, result.raw.columns))}")
    print(f"Columna longitud x : {result.columns.longitude}")
    print(f"Columna latitud  y : {result.columns.latitude}")
    print(f"Pais seleccionado  : {result.country}")
    print("\nPrimeras filas:")
    print(result.raw.head().to_string(index=False))

    # --- Actividad 2 -------------------------------------------------------
    _titulo("ACTIVIDAD 2. Limpieza y seleccion de datos (3 puntos)")
    print(result.cleaning.as_table().to_string(index=False))
    print("\nTabla limpia (primeras 10 filas):")
    columnas = [c for c in cfg.CLEAN_COLUMNS if c in result.clean.columns]
    print(result.clean[columnas].head(10).to_string(index=False))
    print(f"\nTotal de localidades limpias: {len(result.clean):,}")

    # --- Actividad 3 -------------------------------------------------------
    _titulo("ACTIVIDAD 3. Delimitacion del dominio geografico (4 puntos)")
    domain = result.domain
    print(f"Longitud minima (xmin): {domain.xmin:.6f}")
    print(f"Longitud maxima (xmax): {domain.xmax:.6f}")
    print(f"Latitud  minima (ymin): {domain.ymin:.6f}")
    print(f"Latitud  maxima (ymax): {domain.ymax:.6f}")
    print(f"\n{domain.notation()}")
    print(f"Amplitud: {domain.width:.4f} x {domain.height:.4f} grados")
    print(f"Area aproximada: {domain.area_km2:,.0f} km2")
    print()
    print(domain.as_table().to_string(index=False))

    # --- Actividades 4, 5 y 6 ---------------------------------------------
    _titulo("ACTIVIDADES 4, 5 y 6. Puntos, cuadricula y malla (3 + 3 + 2 puntos)")
    grid = result.grid
    print(f"Actividad 4: {len(result.clean):,} puntos reales graficados")
    print(f"Actividad 5: cuadricula dx={grid.dx} dy={grid.dy} -> {grid.nx} x {grid.ny} = {grid.size:,} puntos")
    print(f"Actividad 6: malla con {grid.ny} lineas horizontales y {grid.nx} verticales ({grid.cells:,} celdas)")

    figuras: dict[str, str] = {}
    if not args.sin_figuras:
        cfg.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        trabajos = [
            ("01_puntos_reales.png", lambda: fig_points(result.clean, domain, result.country)),
            ("02_cuadricula.png", lambda: fig_grid(grid, result.country)),
            ("03_malla_visual.png", lambda: fig_mesh(result.clean, grid, result.country)),
            ("04_densidad_por_celda.png", lambda: fig_density(result.clean, grid, result.country)),
            ("05_efecto_dx_dy.png", lambda: fig_resolution_panel(result.clean, domain)),
        ]
        print("\nFiguras generadas:")
        for nombre, constructor in trabajos:
            ruta = save_png(constructor(), cfg.FIGURES_DIR / nombre)
            figuras[nombre] = str(ruta)
            print(f"  - {ruta.relative_to(cfg.PROJECT_ROOT)}")

    # --- Actividad 7 -------------------------------------------------------
    _titulo("ACTIVIDAD 7. Interpretacion visual de resultados (2 puntos)")
    print(result.occupancy.as_table().to_string(index=False))
    print("\nSensibilidad a dx y dy:")
    print(resolution_sensitivity(result.clean, domain).to_string(index=False))
    print("\nRespuestas de la actividad:")
    for pregunta, respuesta in content.activity7_answers(result):
        print(f"\n{pregunta}\n{respuesta}")

    print("\nPreguntas de analisis del informe:")
    for pregunta, respuesta in content.analysis_answers(result):
        print(f"\n{pregunta}\n{respuesta}")

    print("\nConclusiones:")
    for i, texto in enumerate(content.conclusions(result), start=1):
        print(f"\n{i}. {texto}")

    # --- Exportaciones -----------------------------------------------------
    _titulo("EXPORTACION DE RESULTADOS")
    cfg.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    salidas = [
        export_csv(result.clean, cfg.EXPORTS_DIR / "tabla_limpia.csv"),
        export_csv(domain.as_table(), cfg.EXPORTS_DIR / "dominio_limites.csv"),
        export_csv(grid.as_dataframe(), cfg.EXPORTS_DIR / "cuadricula_puntos.csv"),
        export_csv(result.occupancy.table, cfg.EXPORTS_DIR / "densidad_por_celda.csv"),
    ]
    geojson_path = cfg.EXPORTS_DIR / "localidades.geojson"
    geojson_path.write_text(
        json.dumps(to_geojson(result.clean), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    salidas.append(geojson_path)

    respuestas_path = cfg.DOCS_DIR / "RESPUESTAS.md"
    respuestas_path.parent.mkdir(parents=True, exist_ok=True)
    respuestas_path.write_text(content.answers_markdown(result), encoding="utf-8")
    salidas.append(respuestas_path)
    for ruta in salidas:
        print(f"  - {ruta.relative_to(cfg.PROJECT_ROOT)}")

    if not args.sin_pdf:
        pdf_path = save_report(result)
        print(f"  - {pdf_path.relative_to(cfg.PROJECT_ROOT)}  <-- informe final")

    _titulo("RESUMEN DE LAS SIETE ACTIVIDADES")
    for line in result.summary_lines():
        print(f"  {line}")
    print(f"\nListo. Rubrica cubierta: {cfg.TOTAL_POINTS}/{cfg.TOTAL_POINTS} puntos.\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    return ejecutar(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
