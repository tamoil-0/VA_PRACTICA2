# Plan de implementación — Práctica Calificada 02

**Proyecto:** VA_PRACTICA2 — Visualización de dominios geográficos
**Estudiante:** Jhon Marco Aracayo Mamani
**Curso:** Visualización de Datos — Unidad 2 (Técnicas de modelado de dominios)
**Repositorio:** https://github.com/tamoil-0/VA_PRACTICA2
**Estado:** ✅ Fases 1 a 6 completadas · Fase 7 opcional

---

## 1. Objetivo

Entregar la práctica cumpliendo los 20 puntos de la rúbrica y, además, con calidad de
proyecto de software: código modular y documentado, resultados reproducibles con un solo
comando, verificación automática y un informe PDF que el docente pueda leer sin ejecutar
nada.

### Criterios de aceptación

| # | Criterio | Cómo se comprueba |
|---|---|---|
| A1 | Las 7 actividades se resuelven sobre datos geográficos reales | `python main.py` imprime cada actividad con sus cifras |
| A2 | El informe PDF contiene los 14 elementos del "producto final" | `informe/INFORME_PRACTICA_02.pdf`, índice en la página 2 |
| A3 | Los resultados son reproducibles y consistentes entre app, consola e informe | Los tres consumen `pipeline.run_analysis()` |
| A4 | Ninguna afirmación del informe es genérica | `content.py` inyecta cifras del análisis en cada respuesta |
| A5 | El código se puede revisar por partes | Paquete `vizdominios/` con 11 módulos de responsabilidad única |
| A6 | Hay verificación automática | 37 pruebas `pytest`, todas en verde |
| A7 | El repositorio se entiende sin explicación oral | README con instalación, resultados, figuras y mapa rúbrica → código |

---

## 2. Diagnóstico del punto de partida

La primera versión funcionaba, pero tenía problemas que impedían defenderla como trabajo
final:

| Problema | Consecuencia | Solución aplicada |
|---|---|---|
| `app.py` con 1 011 líneas (lógica + CSS + gráficos + PDF) | Imposible revisar o testear por partes | Paquete `vizdominios/` de 11 módulos; `app.py` queda en 70 líneas |
| Sin forma de ejecutar el trabajo sin la interfaz | El docente dependía de levantar Streamlit | `main.py`: un comando imprime todo y genera el informe |
| Interpretaciones y conclusiones escritas a mano | Texto genérico, desconectado de los datos | `content.py` construye cada respuesta con las cifras reales |
| Dataset de solo 35 localidades | Dominio y malla poco representativos | Dataset ampliado a 139 localidades de los 25 departamentos |
| Informe PDF plano, sin carátula ni numeración | No cumplía el "producto final a entregar" | Informe de 17 páginas: carátula institucional, índice, 13 secciones, anexo de código |
| Archivos sueltos en la raíz (`.txt`, PDF duplicado, `__pycache__`) | Repositorio confuso | Limpieza + `.gitignore` + carpetas `assets/ docs/ informe/ salidas/ scripts/ tests/` |
| Cero pruebas | Nada garantizaba que el dominio o la cuadrícula fueran correctos | 37 pruebas sobre dominio, limpieza, métricas y PDF |
| Interpretación solo cualitativa | La Actividad 7 se quedaba en frases | Métricas: densidad por celda, cobertura, haversine, sensibilidad a dx/dy |

---

## 3. Arquitectura implementada

```text
                       ┌──────────────────────┐
   data/*.csv  ───────▶│  dataio.load_dataset │
   CSV de Kaggle       └──────────┬───────────┘
                                  ▼
                       ┌──────────────────────┐   Actividad 1
                       │ domain.detect_columns│   (ColumnMap)
                       └──────────┬───────────┘
                                  ▼
                       ┌──────────────────────┐   Actividad 2
                       │  dataio.clean_data   │   (+ CleaningReport)
                       │  add_geo_groups      │
                       │  filter_geo_data     │
                       └──────────┬───────────┘
                                  ▼
                       ┌──────────────────────┐   Actividad 3
                       │ GeoDomain.from_df    │   D = [xmin,xmax]×[ymin,ymax]
                       └──────────┬───────────┘
                                  ▼
                       ┌──────────────────────┐   Actividad 5
                       │ Grid.from_domain     │   np.meshgrid(dx, dy)
                       └──────────┬───────────┘
                                  ▼
                       ┌──────────────────────┐   Actividad 7
                       │ analysis.cell_occup. │   np.histogram2d
                       └──────────┬───────────┘
                                  ▼
                       ╔══════════════════════╗
                       ║    AnalysisResult    ║  ← una sola fuente de verdad
                       ╚═══┬═══════┬═══════┬══╝
                           ▼       ▼       ▼
                   ui/tabs.py  report.py  tests/
                   charts.py   figures.py
                   maps.py     content.py
```

**Decisión central:** `pipeline.run_analysis()` devuelve un `AnalysisResult` inmutable con
todos los productos intermedios. La app, el script de consola, el informe y los tests
consumen ese objeto, así que es imposible que muestren números distintos.

### Responsabilidad de cada módulo

| Módulo | Líneas aprox. | Responsabilidad | Actividad |
|---|---|---|---|
| `config.py` | 130 | Rutas, metadatos, paleta, candidatos de columnas | — |
| `domain.py` | 320 | `ColumnMap`, `GeoDomain`, `Grid` | 1, 3, 5 |
| `dataio.py` | 300 | Carga, exploración, limpieza auditada, filtros, export | 1, 2 |
| `analysis.py` | 240 | Densidad por celda, haversine, sensibilidad a dx/dy | 7 |
| `figures.py` | 240 | 5 figuras Matplotlib para el informe | 4, 5, 6 |
| `charts.py` | 230 | Gráficos Plotly interactivos | 4, 5, 6 |
| `maps.py` | 160 | Mapas OpenStreetMap (valor agregado) | 4, 5, 6 |
| `content.py` | 420 | Interpretaciones, respuestas, conclusiones, rúbrica | 1, 7 |
| `pipeline.py` | 150 | Orquestador de las 7 actividades | todas |
| `report.py` | 520 | Informe PDF con ReportLab | producto final |
| `ui/` | 480 | Tema, barra lateral y 10 pestañas | todas |

---

## 4. Fases del plan

### ✅ Fase 1 — Modelo de dominio y datos

- [x] `ColumnMap` con detección automática (exacta y parcial) de ciudad, país, lat y lon.
- [x] `GeoDomain` con validación `xmin ≤ xmax`, propiedades derivadas (ancho, alto, centro,
      área en grados² y km²), `padded()`, `contains()`, `rectangle()`, `as_table()`.
- [x] `Grid.from_domain()` con `np.arange` + `np.meshgrid`; cobertura hasta `xmax + dx`.
- [x] `clean_data()` en 5 pasos auditables → `CleaningReport` con el conteo de descartes.
- [x] Enriquecimiento con zona macro (Norte/Centro/Sur) y región natural (Costa/Sierra/Selva).
- [x] Exportadores CSV y GeoJSON (EPSG:4326, orden `[lon, lat]`).
- [x] Dataset ampliado de 35 → 139 localidades con `place_type`.

### ✅ Fase 2 — Visualización

- [x] Armazón común de ejes: longitud en X, latitud en Y, título, etiquetas, cuadrícula de
      fondo, escala 1:1 y rectángulo del dominio (requisitos de las Actividades 4 y 6).
- [x] Figuras Matplotlib (`Agg`, sin GUI): puntos, cuadrícula, malla, densidad y panel de
      resolución.
- [x] Gráficos Plotly equivalentes con hover, leyenda y zoom.
- [x] Malla enviada como un solo trace con separadores `None` (evita cientos de traces).
- [x] Mapas sobre OpenStreetMap sin token: puntos, cuadrícula y malla georreferenciadas.
- [x] Paleta única en `config.PALETTE` para los tres backends (Plotly, Matplotlib, PDF).

### ✅ Fase 3 — Análisis cuantitativo (refuerzo de la Actividad 7)

- [x] `cell_occupancy()` con `np.histogram2d`: conteo por celda, celdas ocupadas/vacías,
      cobertura y celda más densa.
- [x] `nearest_neighbor_km()` con haversine vectorizado (validado contra Lima–Puno ≈ 850 km).
- [x] `resolution_sensitivity()`: tabla comparativa para dx = 0.25, 0.5, 1.0 y 2.0.
- [x] `real_vs_generated()`: comparación explícita puntos observados vs. sintéticos.
- [x] `coordinate_summary()`: mínimos, máximos, media, desviación y rango.

### ✅ Fase 4 — Informe PDF

- [x] Carátula con logos UNAP y EPISI escalados a su proporción original.
- [x] Encabezado y pie con numeración en todas las páginas salvo la carátula.
- [x] Índice de las 13 secciones + resumen de resultados + trazabilidad por actividad.
- [x] Tablas con celdas `Paragraph` (texto largo envuelto, sin desbordes) y cebra suave.
- [x] Las 5 figuras insertadas con relación de aspecto correcta y pie de figura.
- [x] Respuestas de la Actividad 7 y las 7 preguntas de análisis con cifras inyectadas.
- [x] Conclusiones, verificación de la rúbrica (20 pts) y anexo con el código Python.
- [x] Metadatos del PDF (título, autor, asunto) y `KeepTogether` para no cortar respuestas.

### ✅ Fase 5 — Aplicación e interfaz

- [x] `app.py` reducido a orquestación (70 líneas).
- [x] `ui/theme.py`: `set_page_config`, CSS con variables derivadas de la paleta, encabezado,
      leyenda de color, tarjetas de respuesta.
- [x] `ui/sidebar.py`: carga de CSV, país, dx/dy y filtros construidos desde los datos.
- [x] `ui/tabs.py`: 10 pestañas, una por bloque de la práctica; presentación sin lógica.
- [x] Descargas: tabla limpia (CSV), puntos (GeoJSON), informe (PDF), código (`.py`).
- [x] Errores controlados con `EmptySelectionError` y mensajes accionables.

### ✅ Fase 6 — Calidad, reproducibilidad y entrega

- [x] `main.py` con `argparse` (`--csv --pais --dx --dy --region --sin-pdf --sin-figuras`).
- [x] 37 pruebas `pytest` en 3 archivos (dominio, datos, pipeline+informe).
- [x] `docs/RESPUESTAS.md` generado automáticamente: imposible que se desincronice.
- [x] `scripts/descargar_dataset_kaggle.py` para el dataset original.
- [x] Limpieza del repositorio, `.gitignore`, `pytest.ini`, `requirements.txt` comentado.
- [x] README con instalación, resultados, figuras, estructura y mapa rúbrica → código.
- [x] `run_app.bat` y `run_informe.bat` para uso sin consola.

### ⬜ Fase 7 — Extensiones opcionales (fuera del alcance de la práctica)

- [ ] Notebook Jupyter equivalente a `main.py` para presentación en clase.
- [ ] Cuadrícula recortada al contorno real del país (requiere GeoPandas y un shapefile).
- [ ] Clustering DBSCAN y KDE sobre las localidades.
- [ ] Comparación lado a lado de dos regiones en la misma vista.
- [ ] GitHub Actions ejecutando `pytest` en cada push.
- [ ] Despliegue en Streamlit Community Cloud.

> Estas extensiones se dejan fuera a propósito: añaden dependencias pesadas
> (GeoPandas, scikit-learn) y no aportan puntos de rúbrica. Se documentan para que el plan
> refleje lo que se decidió **no** hacer y por qué.

---

## 5. Trazabilidad rúbrica → implementación → evidencia

| Criterio | Pts | Implementación | Evidencia |
|---|---|---|---|
| Exploración del dataset | 3 | `dataio.dataset_overview`, `column_profile` | Informe §2 · pestaña 1 · consola Actividad 1 |
| Limpieza y filtrado | 3 | `dataio.clean_data` + `CleaningReport` | Informe §3 · `salidas/tabla_limpia.csv` |
| Delimitación del dominio | 4 | `domain.GeoDomain` | Informe §4 · `salidas/dominio_limites.csv` |
| Puntos reales | 3 | `figures.fig_points`, `charts.chart_points` | Figura 1 · `docs/figuras/01_puntos_reales.png` |
| Cuadrícula | 3 | `domain.Grid.from_domain` | Figura 2 · `salidas/cuadricula_puntos.csv` |
| Malla | 2 | `figures.fig_mesh`, `charts.chart_mesh` | Figura 3 · `docs/figuras/03_malla_visual.png` |
| Interpretación visual | 2 | `content` + `analysis` | Informe §9-§10 · `docs/RESPUESTAS.md` |
| **Total** | **20** | | Tabla de verificación en el informe §12 |

---

## 6. Riesgos considerados

| Riesgo | Mitigación aplicada |
|---|---|
| El CSV de Kaggle pesa cientos de MB y no entra en GitHub | Dataset propio de 139 localidades con el mismo esquema + script de descarga |
| Otro CSV puede tener nombres de columna distintos | `find_column()` con coincidencia exacta y parcial sobre 5 listas de candidatos |
| `np.arange` excluye el extremo: la cuadrícula podría no cubrir el dominio | Se genera hasta `xmax + dx` / `ymax + dy`; hay un test que lo verifica |
| Un filtro puede dejar la selección vacía y romper el dominio | `EmptySelectionError` con mensaje accionable + validación en `GeoDomain` |
| Una sola localidad hace degenerar la malla (0 celdas) | `cell_occupancy` devuelve resultado vacío controlado; hay test |
| Los textos del informe podrían contradecir los números | Todos se generan desde `content.py` con el propio `AnalysisResult` |
| Matplotlib sin interfaz gráfica falla en servidor | Backend `Agg` fijado antes de importar `pyplot` |

---

## 7. Verificación final

```bash
python -m pytest        # 37 passed
python main.py          # 7 actividades + 5 figuras + 5 exportaciones + informe PDF
python -m streamlit run app.py
```

Resultado de la corrida por defecto (Perú, dx = dy = 0.5): 139 localidades limpias,
dominio `D = [-81.2719, -69.0417] × [-18.0066, -3.5011]`, 806 puntos de cuadrícula,
750 celdas de malla, 15.7 % de cobertura e informe de 17 páginas.
