"""Textos interpretativos de la practica, generados con los datos reales.

Este modulo es la unica fuente de las respuestas, interpretaciones y
conclusiones del trabajo. La app Streamlit, el informe PDF y la documentacion
en Markdown consumen las mismas funciones, de modo que lo que el docente lee en
el PDF es exactamente lo que ve en la aplicacion.

Casi todas las respuestas se construyen con las cifras del analisis
(``AnalysisResult``), no con texto fijo: si cambia el pais, el filtro o el valor
de dx, las interpretaciones se recalculan.
"""

from __future__ import annotations

from . import config as cfg
from .analysis import nearest_neighbor_km
from .pipeline import AnalysisResult


# ---------------------------------------------------------------------------
# Descripcion del dataset (Actividad 1)
# ---------------------------------------------------------------------------
def dataset_description(result: AnalysisResult) -> str:
    """Parrafo descriptivo del dataset utilizado."""
    return (
        f"El trabajo utiliza el dataset '{cfg.DATASET_NAME}' publicado en "
        f"{cfg.DATASET_SOURCE} ({cfg.DATASET_URL}), que reune informacion "
        "geografica de paises, regiones, provincias, ciudades y distritos con sus "
        "coordenadas de longitud y latitud en formato CSV. El archivo procesado "
        f"({result.source_label}) contiene {len(result.raw):,} registros y "
        f"{len(result.raw.columns)} columnas; de ellas, "
        f"'{result.columns.longitude}' aporta la coordenada x (longitud) y "
        f"'{result.columns.latitude}' la coordenada y (latitud), que son las dos "
        "variables espaciales necesarias para delimitar un dominio y construir "
        f"cuadriculas y mallas. Para el analisis se selecciono {result.country}, "
        "tal como recomienda la practica."
    )


# ---------------------------------------------------------------------------
# Interpretacion de la distribucion (Actividad 4)
# ---------------------------------------------------------------------------
def distribution_comment(result: AnalysisResult) -> str:
    """Comentario interpretativo de la distribucion espacial observada."""
    data = result.clean
    domain = result.domain
    partes: list[str] = [
        f"Los {len(data):,} puntos reales se distribuyen de forma claramente "
        f"irregular dentro del dominio, que abarca {domain.width:.2f} grados de "
        f"longitud por {domain.height:.2f} grados de latitud "
        f"(aproximadamente {domain.area_km2:,.0f} km2)."
    ]

    if cfg.COL_NATURAL in data.columns:
        conteo = data[cfg.COL_NATURAL].value_counts()
        principal = conteo.index[0]
        pct = 100.0 * conteo.iloc[0] / len(data)
        detalle = ", ".join(f"{k}: {v}" for k, v in conteo.items())
        partes.append(
            f"Por region natural el reparto es {detalle}; la mayor concentracion "
            f"corresponde a la {principal} con {pct:.1f} % de las localidades, lo "
            "que reproduce el patron de poblamiento del pais y no una distribucion "
            "aleatoria."
        )

    if cfg.COL_REGION in data.columns and data[cfg.COL_REGION].notna().any():
        top = data[cfg.COL_REGION].value_counts().head(3)
        partes.append(
            "Las regiones con mas registros son "
            + ", ".join(f"{k} ({v})" for k, v in top.items())
            + "."
        )

    vecinos = nearest_neighbor_km(data)
    if vecinos.notna().any():
        partes.append(
            f"La distancia media al vecino mas cercano es de {vecinos.mean():.1f} km "
            f"(minima {vecinos.min():.1f} km y maxima {vecinos.max():.1f} km), "
            "evidencia numerica de que existen zonas densas y zonas practicamente "
            "vacias dentro del mismo dominio."
        )

    ocupacion = result.occupancy
    if ocupacion.total_cells:
        partes.append(
            f"Al superponer la malla, solo {ocupacion.occupied_cells:,} de las "
            f"{ocupacion.total_cells:,} celdas contienen al menos una localidad "
            f"({ocupacion.occupancy_pct:.1f} % de cobertura), y la celda mas densa "
            f"concentra {ocupacion.max_count} puntos: el dominio rectangular cubre "
            "mucho mas territorio del que realmente esta ocupado por localidades "
            "registradas."
        )
    return " ".join(partes)


# ---------------------------------------------------------------------------
# Actividad 7: interpretacion visual de resultados
# ---------------------------------------------------------------------------
def activity7_answers(result: AnalysisResult) -> list[tuple[str, str]]:
    """Respuestas a las cuatro preguntas de la Actividad 7."""
    domain = result.domain
    grid = result.grid
    ocupacion = result.occupancy
    return [
        (
            "a) Que representa el dominio geografico construido?",
            f"Representa el rectangulo minimo (bounding box) que contiene todas las "
            f"coordenadas seleccionadas: {domain.notation(2)}. No es un mapa del "
            f"pais, es el area de analisis: fija el marco espacial dentro del cual "
            f"tienen sentido la cuadricula, la malla y cualquier calculo posterior. "
            f"Sus cuatro limites son interpretables: xmin es el extremo occidental, "
            f"xmax el oriental, ymin el mas al sur y ymax el mas al norte de las "
            f"{len(result.clean):,} localidades analizadas.",
        ),
        (
            "b) Que diferencia existe entre los puntos reales y los de la cuadricula?",
            f"Los puntos reales son observaciones: {len(result.clean):,} localidades "
            f"que existen en el territorio, con distribucion irregular determinada por "
            f"el poblamiento. Los {grid.size:,} puntos de la cuadricula son sinteticos: "
            f"los genera numpy.meshgrid a intervalos constantes (dx = {grid.dx}, "
            f"dy = {grid.dy}) y no representan ninguna ciudad, sino posiciones de "
            f"referencia del espacio. Los primeros responden 'donde estan los hechos'; "
            f"los segundos aportan el sistema de medida que permite comparar zonas.",
        ),
        (
            "c) Que utilidad tiene una malla en la visualizacion de datos espaciales?",
            f"La malla convierte un espacio continuo en unidades comparables. En este "
            f"caso genera {grid.cells:,} celdas y permite contar cuantas localidades "
            f"caen en cada una: {ocupacion.occupied_cells:,} celdas resultan ocupadas "
            f"y {ocupacion.empty_cells:,} quedan vacias. Ademas sirve como referencia "
            f"visual (facilita estimar distancias y ubicar un punto), como base de "
            f"agregacion (densidad, mapas de calor, conteos por celda) y como soporte "
            f"para detectar vacios de cobertura que un grafico de puntos suelto no "
            f"muestra con claridad.",
        ),
        (
            "d) Como podria aplicarse en un problema de Ingenieria de Sistemas?",
            "El esquema dominio + cuadricula + malla es la base de cualquier analisis "
            "territorial computacional. Aplicaciones directas: (1) cobertura de "
            "servicios digitales, marcando las celdas sin atencion; (2) ubicacion "
            "optima de sensores IoT o antenas, usando una celda por sensor para no "
            "duplicar cobertura; (3) analisis de la distribucion de usuarios de una "
            "plataforma para dimensionar servidores o centros de distribucion; "
            "(4) diseno de rutas y logistica, calculando costos entre celdas; "
            "(5) tableros de decision territorial, donde cada celda es una fila "
            "agregable en una base de datos espacial.",
        ),
    ]


# ---------------------------------------------------------------------------
# Preguntas de analisis del informe (seccion 10 de la practica)
# ---------------------------------------------------------------------------
def analysis_answers(result: AnalysisResult) -> list[tuple[str, str]]:
    """Respuestas a las siete preguntas de analisis solicitadas en el informe."""
    domain = result.domain
    grid = result.grid
    fino = _grid_size_for(result, 0.25)
    grueso = _grid_size_for(result, 2.0)
    return [
        (
            "1. Por que es importante delimitar un dominio antes de construir una "
            "visualizacion espacial?",
            f"Porque define el area de estudio y, con ella, la escala de todo lo "
            f"demas. Sin dominio no se puede fijar el rango de los ejes ni generar "
            f"una cuadricula acotada, y el grafico incluiria espacio vacio que "
            f"comprime los datos utiles. Aqui el dominio {domain.notation(2)} recorta "
            f"el analisis a {domain.width:.2f} x {domain.height:.2f} grados, lo que "
            f"garantiza que la cuadricula, la malla y las metricas de densidad se "
            f"calculen sobre el territorio observado y no sobre el planeta completo.",
        ),
        (
            "2. Que informacion aporta el grafico de puntos reales?",
            "Aporta la ubicacion y la forma de la distribucion: donde hay "
            "concentracion, donde hay vacios y que estructura describe el conjunto. "
            "En el caso analizado los puntos dibujan el eje costero y los corredores "
            "andinos, revelando que la distribucion es agrupada y no uniforme. Es la "
            "visualizacion que responde 'donde ocurre el fenomeno' antes de cualquier "
            "modelo.",
        ),
        (
            "3. Que representa una cuadricula de puntos en visualizacion de datos?",
            f"Representa un muestreo regular del espacio: un conjunto de posiciones "
            f"generadas cada dx grados en horizontal y dy en vertical. No son datos "
            f"observados, son un sistema de referencia. En este trabajo la cuadricula "
            f"tiene {grid.nx} columnas por {grid.ny} filas ({grid.size:,} nodos) y "
            f"sirve para discretizar el dominio, es decir, para pasar de un espacio "
            f"continuo a un conjunto finito de unidades analizables.",
        ),
        (
            "4. Que diferencia existe entre una cuadricula y una malla?",
            f"La cuadricula es el conjunto de puntos ({grid.size:,} nodos aqui); la "
            f"malla es la estructura que resulta de unir esos puntos con "
            f"{grid.ny} lineas horizontales y {grid.nx} lineas verticales, generando "
            f"{grid.cells:,} celdas. La cuadricula aporta posiciones discretas; la "
            f"malla aporta topologia (vecindad, celdas, bordes) y por eso permite "
            f"agregar, contar y comparar por zona.",
        ),
        (
            "5. Que ocurre visualmente si se reduce el valor de dx y dy?",
            f"La resolucion aumenta y el detalle es mayor, pero el costo crece de "
            f"forma cuadratica y la lectura se satura. Con dx = dy = {grid.dx} se "
            f"generan {grid.size:,} nodos; al bajar a 0.25 se pasa a "
            f"{fino['puntos']:,} nodos y {fino['celdas']:,} celdas, de las cuales solo "
            f"{fino['cobertura']:.1f} % quedan ocupadas: las lineas se juntan tanto "
            f"que tapan los puntos reales y la mayoria de celdas queda vacia.",
        ),
        (
            "6. Que ocurre visualmente si se aumenta el valor de dx y dy?",
            f"La visualizacion se simplifica y gana legibilidad, pero pierde "
            f"precision espacial. Con dx = dy = 2.0 la cuadricula baja a "
            f"{grueso['puntos']:,} nodos y {grueso['celdas']:,} celdas con "
            f"{grueso['cobertura']:.1f} % de ocupacion: cada celda agrupa localidades "
            f"muy distantes entre si, se ocultan diferencias internas y aparece el "
            f"riesgo de agregacion excesiva (varias ciudades distintas se leen como un "
            f"solo bloque).",
        ),
        (
            "7. Como puede ayudar esta visualizacion en la toma de decisiones dentro "
            "de Ingenieria de Sistemas?",
            f"Convierte coordenadas en unidades de decision. Cada una de las "
            f"{grid.cells:,} celdas puede almacenar indicadores (usuarios, incidencias, "
            f"cobertura, latencia) y volverse una fila de una base de datos espacial; "
            f"sobre esa estructura se priorizan inversiones, se ubican sensores o "
            f"antenas, se disenan rutas y se detectan zonas desatendidas. En este "
            f"analisis, las {result.occupancy.empty_cells:,} celdas sin localidades "
            f"son exactamente el tipo de hallazgo que orienta una decision: senalan "
            f"donde no hay presencia registrada.",
        ),
    ]


def _grid_size_for(result: AnalysisResult, delta: float) -> dict[str, float]:
    """Metricas de la cuadricula para un paso alternativo (respuestas 5 y 6)."""
    from .analysis import cell_occupancy
    from .domain import Grid

    grid = Grid.from_domain(result.domain, delta, delta)
    occupancy = cell_occupancy(result.clean, grid)
    return {
        "puntos": grid.size,
        "celdas": grid.cells,
        "cobertura": occupancy.occupancy_pct,
    }


# ---------------------------------------------------------------------------
# Conclusiones
# ---------------------------------------------------------------------------
def conclusions(result: AnalysisResult) -> list[str]:
    """Conclusiones del trabajo, alineadas con la conclusion esperada."""
    domain = result.domain
    grid = result.grid
    return [
        f"El modelado de dominios permitio pasar de un CSV de "
        f"{len(result.raw):,} registros a un area de analisis explicita: "
        f"{domain.notation(2)}, obtenida solo con los minimos y maximos de longitud "
        f"y latitud de las {len(result.clean):,} localidades limpias.",
        f"La cuadricula regular (dx = {grid.dx}, dy = {grid.dy}) discretizo ese "
        f"dominio continuo en {grid.size:,} nodos, y la malla lo organizo en "
        f"{grid.cells:,} celdas comparables entre si. Ese paso de continuo a discreto "
        f"es lo que habilita medir densidad y cobertura.",
        f"La superposicion de puntos reales y malla mostro que la distribucion "
        f"territorial es fuertemente irregular: apenas "
        f"{result.occupancy.occupancy_pct:.1f} % de las celdas contiene alguna "
        f"localidad. El dominio delimita el maximo posible, no lo efectivamente "
        f"ocupado, y esa diferencia es en si misma un resultado del analisis.",
        "El valor de dx y dy no es un detalle estetico sino una decision analitica: "
        "define el nivel de agregacion, el costo computacional y el riesgo de ocultar "
        "o exagerar patrones. Elegirlo requiere conocer la escala del fenomeno.",
        "Finalmente, las tres visualizaciones son complementarias y no sustitutas: "
        "los puntos muestran los hechos, la cuadricula aporta el sistema de medida y "
        "la malla ofrece la estructura de agregacion. Sobre esa base se construyen "
        "aplicaciones de Ingenieria de Sistemas como cobertura de servicios, redes de "
        "sensores IoT, planificacion de rutas y tableros de decision territorial.",
    ]


# ---------------------------------------------------------------------------
# Verificacion de la rubrica
# ---------------------------------------------------------------------------
def rubric_rows(result: AnalysisResult) -> list[list[str]]:
    """Trazabilidad rubrica -> evidencia concreta en el proyecto."""
    grid = result.grid
    return [
        [
            "Exploracion del dataset",
            "3",
            f"Actividad 1: {len(result.raw):,} registros y {len(result.raw.columns)} columnas "
            f"identificadas; columnas de coordenadas detectadas automaticamente "
            f"({result.columns.longitude}, {result.columns.latitude}). "
            "Pestana 'Exploracion' de la app y seccion 1 del informe.",
        ],
        [
            "Limpieza y filtrado de datos",
            "3",
            f"Actividad 2: filtro de pais ({result.country}), conversion numerica de "
            f"coordenadas, eliminacion de nulos, rangos invalidos y duplicados; "
            f"tabla final de {len(result.clean):,} filas con Ciudad, Pais, Latitud y "
            "Longitud, mas auditoria paso a paso.",
        ],
        [
            "Delimitacion del dominio",
            "4",
            f"Actividad 3: {result.domain.notation(4)} con tabla de los cuatro limites "
            "e interpretacion de cada uno (occidental, oriental, sur y norte).",
        ],
        [
            "Visualizacion de puntos reales",
            "3",
            "Actividad 4: dispersion con longitud en X, latitud en Y, titulo, "
            "etiquetas de ejes, cuadricula de fondo, leyenda e interpretacion "
            "cuantitativa de la distribucion.",
        ],
        [
            "Generacion de cuadricula",
            "3",
            f"Actividad 5: cuadricula regular con np.meshgrid, dx = {grid.dx} y "
            f"dy = {grid.dy}, {grid.nx} x {grid.ny} = {grid.size:,} puntos dentro del "
            "dominio definido.",
        ],
        [
            "Construccion de malla",
            "2",
            f"Actividad 6: {grid.ny} lineas horizontales y {grid.nx} verticales, "
            "rectangulo del dominio dibujado y puntos reales superpuestos.",
        ],
        [
            "Interpretacion visual",
            "2",
            "Actividad 7: las cuatro preguntas respondidas con cifras del propio "
            "analisis, mas las siete preguntas de analisis y las conclusiones.",
        ],
    ]


# ---------------------------------------------------------------------------
# Codigo reproducible (anexo del informe y pestana 'Codigo' de la app)
# ---------------------------------------------------------------------------
def code_annex(result: AnalysisResult) -> str:
    """Version minima y autocontenida del codigo, siguiendo el codigo base."""
    return f'''# ---------------------------------------------------------------
# Practica Calificada 02 - Visualizacion de dominios geograficos
# Version minima y reproducible del flujo completo (7 actividades)
# ---------------------------------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. CARGA DE DATOS -------------------------------------------------
df = pd.read_csv("data/{cfg.DEFAULT_DATASET.name}")
print(df.head())
print(df.info())
print(df.columns)

# 2. FILTRADO Y LIMPIEZA -------------------------------------------
pais = "{result.country}"
datos = df[df["{result.columns.country}"] == pais]
datos = datos[["{result.columns.city}", "{result.columns.country}",
               "{result.columns.latitude}", "{result.columns.longitude}"]]
datos["{result.columns.latitude}"] = pd.to_numeric(datos["{result.columns.latitude}"], errors="coerce")
datos["{result.columns.longitude}"] = pd.to_numeric(datos["{result.columns.longitude}"], errors="coerce")
datos = datos.dropna(subset=["{result.columns.latitude}", "{result.columns.longitude}"])
datos = datos.drop_duplicates()
print("Registros seleccionados:", len(datos))

# 3. DELIMITACION DEL DOMINIO --------------------------------------
x = datos["{result.columns.longitude}"]
y = datos["{result.columns.latitude}"]
xmin, xmax = x.min(), x.max()
ymin, ymax = y.min(), y.max()
print("DOMINIO GEOGRAFICO")
print("Longitud minima:", xmin, "| Longitud maxima:", xmax)
print("Latitud minima :", ymin, "| Latitud maxima :", ymax)

# 4. PUNTOS GEOGRAFICOS REALES ------------------------------------
plt.figure(figsize=(8, 6))
plt.scatter(x, y, s=18, color="{cfg.PALETTE['real']}")
plt.title("Puntos geograficos reales - " + pais)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.grid(True)
plt.show()

# 5. CUADRICULA DE PUNTOS -----------------------------------------
dx = dy = {result.dx}
x_grid = np.arange(xmin, xmax + dx, dx)
y_grid = np.arange(ymin, ymax + dy, dy)
X, Y = np.meshgrid(x_grid, y_grid)

plt.figure(figsize=(8, 6))
plt.scatter(X, Y, s=8, color="{cfg.PALETTE['generated']}")
plt.title("Cuadricula de puntos del dominio - " + pais)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.grid(True)
plt.show()

# 6. MALLA VISUAL --------------------------------------------------
plt.figure(figsize=(8, 6))
for i in range(Y.shape[0]):                      # lineas horizontales
    plt.plot(X[i, :], Y[i, :], linewidth=0.5, color="{cfg.PALETTE['mesh']}")
for j in range(X.shape[1]):                      # lineas verticales
    plt.plot(X[:, j], Y[:, j], linewidth=0.5, color="{cfg.PALETTE['mesh']}")
plt.gca().add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                                  fill=False, edgecolor="{cfg.PALETTE['domain']}", linewidth=1.5))
plt.scatter(x, y, s=18, color="{cfg.PALETTE['real']}")   # puntos reales superpuestos
plt.title("Malla visual del dominio con puntos reales - " + pais)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.grid(True)
plt.show()

# 7. INTERPRETACION CUANTITATIVA ----------------------------------
conteo, _, _ = np.histogram2d(x, y, bins=[x_grid, y_grid])
print("Celdas de la malla        :", conteo.size)
print("Celdas con puntos reales  :", int((conteo > 0).sum()))
print("Cobertura de la malla     : {{:.1f}} %".format(100 * (conteo > 0).sum() / conteo.size))
'''


def systems_applications() -> list[tuple[str, str]]:
    """Casos de aplicacion en Ingenieria de Sistemas (Actividad 7, punto d)."""
    return [
        (
            "Cobertura de servicios digitales",
            "Cada celda de la malla se marca como atendida o desatendida segun los "
            "puntos de servicio que contiene; las celdas vacias definen la agenda de "
            "expansion.",
        ),
        (
            "Ubicacion de sensores IoT",
            "La cuadricula propone posiciones candidatas equidistantes y la malla "
            "verifica que no queden zonas sin sensor ni sensores redundantes.",
        ),
        (
            "Distribucion de usuarios de una plataforma",
            "Agregando usuarios por celda se obtiene un mapa de demanda que permite "
            "dimensionar servidores, CDN o centros de distribucion.",
        ),
        (
            "Diseno de rutas y logistica",
            "Las celdas se convierten en nodos de un grafo con costos de "
            "desplazamiento, base para algoritmos de rutas mas cortas.",
        ),
        (
            "Tableros de decision territorial",
            "Cada celda es una fila con indicadores comparables, lo que hace posible "
            "priorizar inversiones con criterios espaciales explicitos.",
        ),
    ]


def report_index() -> list[tuple[str, str]]:
    """Indice del informe, en el orden que exige el 'producto final a entregar'."""
    return [
        ("Caratula", "Datos generales de la practica y del estudiante"),
        ("1", "Descripcion y enlace del dataset utilizado"),
        ("2", "Columnas principales del dataset (Actividad 1)"),
        ("3", "Pais seleccionado y tabla limpia (Actividad 2)"),
        ("4", "Tabla de limites del dominio geografico (Actividad 3)"),
        ("5", "Grafico de puntos geograficos reales (Actividad 4)"),
        ("6", "Grafico de cuadricula de puntos (Actividad 5)"),
        ("7", "Grafico de malla visual (Actividad 6)"),
        ("8", "Analisis de densidad y sensibilidad a dx/dy"),
        ("9", "Interpretacion de resultados (Actividad 7)"),
        ("10", "Preguntas de analisis"),
        ("11", "Conclusiones"),
        ("12", "Verificacion de la rubrica"),
        ("13", "Anexo: codigo utilizado en Python"),
    ]


def answers_markdown(result: AnalysisResult) -> str:
    """Documento Markdown con todas las respuestas (docs/RESPUESTAS.md).

    Se genera desde las mismas funciones que alimentan el PDF y la app, por lo
    que nunca puede quedar desincronizado del analisis.
    """
    domain = result.domain
    grid = result.grid
    lineas: list[str] = [
        "# Respuestas de la Practica Calificada 02",
        "",
        "> Documento generado automaticamente por `python main.py` a partir del "
        "analisis ejecutado. Las cifras corresponden a la corrida por defecto "
        f"({result.country}, dx = {grid.dx}, dy = {grid.dy}).",
        "",
        "## Datos de la corrida",
        "",
        "| Indicador | Valor |",
        "|---|---|",
    ]
    lineas += [f"| {k} | {v} |" for k, v in numeric_highlights(result)]

    lineas += [
        "",
        "## Actividad 1. Exploracion de la base de datos",
        "",
        dataset_description(result),
        "",
        "| Pregunta | Respuesta |",
        "|---|---|",
        f"| a) Cuantos registros contiene el archivo? | {len(result.raw):,} |",
        f"| b) Que columnas contiene? | {', '.join(f'`{c}`' for c in result.raw.columns)} |",
        f"| c) Que columnas son las coordenadas? | `{result.columns.longitude}` (x, longitud) y "
        f"`{result.columns.latitude}` (y, latitud) |",
        f"| d) Que pais se selecciona? | {result.country} |",
        "",
        "## Actividad 2. Limpieza y seleccion de datos",
        "",
        "| Paso de limpieza | Registros |",
        "|---|---|",
    ]
    for _, row in result.cleaning.as_table().iterrows():
        lineas.append(f"| {row.iloc[0]} | {row.iloc[1]} |")

    lineas += [
        "",
        f"Tabla final: **{len(result.clean):,} localidades** con Ciudad o localidad, Pais, "
        "Region, Latitud y Longitud (`salidas/tabla_limpia.csv`).",
        "",
        "## Actividad 3. Delimitacion del dominio geografico",
        "",
        f"```text\n{domain.notation()}\n```",
        "",
        "| Parametro | Valor | Interpretacion |",
        "|---|---|---|",
    ]
    for _, row in domain.as_table().iterrows():
        lineas.append(f"| {row.iloc[0]} | {row.iloc[1]:.4f} | {row.iloc[2]} |")

    lineas += [
        "",
        "## Actividad 7. Interpretacion visual de resultados",
        "",
    ]
    for pregunta, respuesta in activity7_answers(result):
        lineas += [f"### {pregunta}", "", respuesta, ""]

    lineas += ["## Preguntas de analisis del informe", ""]
    for pregunta, respuesta in analysis_answers(result):
        lineas += [f"### {pregunta}", "", respuesta, ""]

    lineas += ["## Conclusiones", ""]
    for i, texto in enumerate(conclusions(result), start=1):
        lineas += [f"{i}. {texto}", ""]

    lineas += [
        "## Verificacion de la rubrica",
        "",
        "| Criterio | Pts | Evidencia |",
        "|---|---|---|",
    ]
    lineas += [f"| {c} | {p} | {e} |" for c, p, e in rubric_rows(result)]
    lineas += ["", f"**Total: {cfg.TOTAL_POINTS} puntos cubiertos.**", ""]
    return "\n".join(lineas)


def numeric_highlights(result: AnalysisResult) -> list[tuple[str, str]]:
    """Cifras clave del analisis, usadas como tarjetas en la app y en el informe."""
    vecinos = nearest_neighbor_km(result.clean)
    promedio = f"{vecinos.mean():.1f} km" if vecinos.notna().any() else "n/d"
    return [
        ("Registros del archivo", f"{len(result.raw):,}"),
        ("Localidades limpias", f"{len(result.clean):,}"),
        ("Dominio (grados)", f"{result.domain.width:.2f} x {result.domain.height:.2f}"),
        ("Area aproximada", f"{result.domain.area_km2:,.0f} km2"),
        ("Puntos de cuadricula", f"{result.grid.size:,}"),
        ("Celdas de la malla", f"{result.grid.cells:,}"),
        ("Cobertura de la malla", f"{result.occupancy.occupancy_pct:.1f} %"),
        ("Vecino mas cercano (promedio)", promedio),
    ]
