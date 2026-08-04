# Practica calificada 02 - Unidad 2

## Visualizacion de dominios geograficos mediante puntos, cuadriculas y mallas

Este proyecto resuelve de forma completa la practica de Visualizacion de Datos. La aplicacion esta hecha en Python con Streamlit y permite cargar un CSV geografico, filtrar un pais, filtrar por regiones, ciudades, zona macro y region natural, limpiar coordenadas, calcular el dominio geografico, construir puntos reales, generar una cuadricula, trazar una malla visual sobre graficos y sobre mapa real, y descargar un informe PDF.

Dataset indicado en la practica:

`Geolocation Data [Longitude Latitude]`  
Fuente: Kaggle  
Enlace: https://www.kaggle.com/datasets/liewyousheng/geolocation

Si no se sube un CSV, la app usa `data/peru_geolocation_sample.csv`, una muestra local de localidades del Peru para que el trabajo funcione inmediatamente.

## Como ejecutar la app

Opcion recomendada en Windows:

1. Abrir la carpeta del proyecto.
2. Hacer doble clic en `run_app.bat`.
3. Esperar a que se abra el navegador.

Opcion por consola:

```powershell
pip install -r requirements.txt
python -m streamlit run app.py
```

La app se abre en una URL local como:

```text
http://localhost:8501
```

Si el puerto 8501 ya esta ocupado, el lanzador `run_app.bat` busca otro puerto disponible.

## Filtros disponibles

La app no trabaja solo con Peru completo. Peru es el pais seleccionado por defecto porque asi lo recomienda la practica, pero dentro de ese pais se puede filtrar de forma dinamica por:

- Regiones o departamentos: por ejemplo Puno, Lima, Piura, Arequipa, Loreto.
- Zona macro: Norte, Centro o Sur.
- Region natural: Costa, Sierra o Selva.
- Ciudades o localidades especificas.

Cada filtro recalcula automaticamente:

- Tabla limpia.
- Limites del dominio geografico.
- Puntos reales.
- Cuadricula.
- Malla visual.
- Mapas interactivos.
- Informe PDF.

Esto significa que si se elige solo Puno, la cuadricula y la malla ya no se construyen sobre todo Peru, sino sobre el dominio geografico de Puno filtrado.

## Estructura del proyecto

```text
2unidad/
  app.py
  README.md
  requirements.txt
  run_app.bat
  run_app.ps1
  data/
    peru_geolocation_sample.csv
  practica_calificada_02-Unidad2_visualizacion_datos.pdf
```

## Cumplimiento de actividades de la practica

| Actividad | Cumple | Como se cumple | Donde esta en la app |
|---|---|---|---|
| Actividad 1: Exploracion de la base de datos | Si cumple | La app carga el CSV, cuenta registros, lista columnas y detecta automaticamente ciudad, pais, latitud y longitud. | Pestana `Exploracion` |
| Actividad 2: Limpieza y seleccion de datos | Si cumple | Filtra el pais seleccionado y ademas permite filtrar por region, ciudad, Norte/Centro/Sur y Costa/Sierra/Selva; convierte latitud y longitud a numeros; elimina registros vacios o inconsistentes; muestra tabla limpia. | Pestana `Limpieza` y barra lateral |
| Actividad 3: Delimitacion del dominio geografico | Si cumple | Calcula `xmin`, `xmax`, `ymin`, `ymax` y define el dominio rectangular `D = [xmin, xmax] x [ymin, ymax]`. | Pestana `Dominio` |
| Actividad 4: Visualizacion de puntos reales | Si cumple | Genera un grafico de dispersion con longitud en X, latitud en Y, titulo, etiquetas, puntos visibles y cuadricula de fondo. Tambien muestra los puntos sobre OpenStreetMap. | Pestana `Visualizaciones > Puntos reales` y `Mapa > Localidades` |
| Actividad 5: Generacion de cuadricula | Si cumple | Genera una cuadricula regular dentro del dominio usando `dx` y `dy`, configurables desde la barra lateral. La cuadricula se ve en grafico cartesiano y sobre mapa real. | Pestana `Visualizaciones > Cuadricula` y `Mapa > Cuadricula en mapa` |
| Actividad 6: Construccion de malla visual | Si cumple | Dibuja lineas horizontales y verticales, rectangulo del dominio y puntos reales superpuestos. Tambien se visualiza la malla encima del mapa. | Pestana `Visualizaciones > Malla` y `Mapa > Malla en mapa` |
| Actividad 7: Interpretacion visual | Si cumple | Responde las preguntas de interpretacion y preguntas de analisis con explicaciones claras. | Pestana `Interpretacion` |
| Producto final | Si cumple | Genera un informe PDF con caratula, dataset, tablas, graficos, interpretacion, conclusiones y codigo base. | Boton `Descargar informe PDF completo` |
| Codigo Python | Si cumple | El codigo principal esta en `app.py` y tambien se muestra un codigo base reproducible. | Pestana `Codigo` |

## Respuestas de la Actividad 1

### a) Cuantos registros contiene el archivo utilizado?

La cantidad de registros depende del archivo CSV cargado. La aplicacion lo calcula automaticamente y lo muestra en la parte superior como `Registros del archivo`.

Con el archivo de muestra incluido en el proyecto, el dataset contiene 35 registros de localidades peruanas.

### b) Que columnas contiene la base de datos?

La aplicacion muestra todas las columnas en la pestana `Exploracion`. En el dataset de muestra se tienen estas columnas:

- `city_name`
- `country_name`
- `region_name`
- `latitude`
- `longitude`

### c) Que columnas representan las coordenadas geograficas?

Las coordenadas geograficas estan representadas por:

- Latitud: `latitude`
- Longitud: `longitude`

En la app, estas columnas se renombran en la tabla limpia como `Latitud` y `Longitud`.

### d) Que pais o region se seleccionara para el analisis?

Se selecciona Peru por defecto, tal como recomienda la practica. Ademas, la app permite seleccionar regiones, ciudades, zonas macro y regiones naturales. Por ejemplo, se puede analizar solo el sur, solo Puno, solo la costa o solo un grupo de ciudades.

## Respuestas de la Actividad 2

La tabla limpia contiene como minimo:

- Ciudad o localidad
- Pais
- Latitud
- Longitud

Si existe una columna de region, tambien se incluye como `Region`.

En esta version tambien se agregan columnas de apoyo para analisis:

- `Zona macro`: Norte, Centro o Sur.
- `Region natural`: Costa, Sierra o Selva.

La limpieza se realiza asi:

- Se filtran los registros del pais seleccionado.
- Se convierten latitud y longitud a valores numericos.
- Se eliminan registros con coordenadas vacias.
- Se eliminan registros inconsistentes que no pueden convertirse a numero.
- Se eliminan duplicados basados en localidad y coordenadas.

Esto se visualiza en la pestana `Limpieza`.

## Respuestas de la Actividad 3

El dominio geografico se calcula a partir de las coordenadas filtradas:

```text
xmin = longitud minima
xmax = longitud maxima
ymin = latitud minima
ymax = latitud maxima
```

Luego se define:

```text
D = [xmin, xmax] x [ymin, ymax]
```

Interpretacion:

- `Longitud minima`: limite occidental del dominio.
- `Longitud maxima`: limite oriental del dominio.
- `Latitud minima`: limite sur del dominio.
- `Latitud maxima`: limite norte del dominio.

La tabla completa aparece en la pestana `Dominio`.

## Respuestas de la Actividad 4

El grafico de puntos reales representa las ciudades o localidades obtenidas del dataset. Cada punto tiene:

- Longitud en el eje X.
- Latitud en el eje Y.
- Titulo descriptivo.
- Etiquetas de ejes.
- Puntos visibles.
- Cuadricula de fondo.
- Informacion interactiva al pasar el cursor.

Interpretacion: el grafico permite observar como se distribuyen las localidades dentro del territorio seleccionado. En el caso de Peru, se observan puntos distribuidos desde la costa norte y sur hasta la sierra y selva, lo cual muestra una cobertura territorial amplia.

## Respuestas de la Actividad 5

La cuadricula regular se genera dentro del dominio geografico usando separaciones:

```text
dx = 0.5
dy = 0.5
```

En la app estos valores se pueden modificar con controles deslizantes. La cuadricula permite dividir el territorio en intervalos constantes para analizar el espacio de forma ordenada.

La visualizacion esta en `Visualizaciones > Cuadricula` y tambien en `Mapa > Cuadricula en mapa`. En el mapa se observa claramente que los puntos generados cubren el rectangulo del dominio filtrado.

## Respuestas de la Actividad 6

La malla visual se construye a partir de la cuadricula. Para ello:

- Se trazan lineas horizontales.
- Se trazan lineas verticales.
- Se dibuja el dominio rectangular.
- Se superponen los puntos reales.

La malla facilita la comparacion espacial porque permite ubicar los puntos reales dentro de una estructura regular. Esta visualizacion esta en `Visualizaciones > Malla` y tambien en `Mapa > Malla en mapa`, donde se aprecia la malla superpuesta sobre OpenStreetMap.

## Respuestas de la Actividad 7

### a) Que representa el dominio geografico construido?

Representa el rectangulo geografico minimo que contiene todas las localidades seleccionadas. Es decir, delimita el area de analisis usando los valores minimos y maximos de latitud y longitud.

### b) Que diferencia existe entre los puntos reales y los puntos generados en la cuadricula?

Los puntos reales provienen del dataset y representan ciudades o localidades existentes. Los puntos generados en la cuadricula no representan ciudades reales; son posiciones matematicas creadas a intervalos regulares para organizar el dominio.

### c) Que utilidad tiene una malla en la visualizacion de datos espaciales?

Una malla ayuda a dividir el territorio en zonas, facilita la lectura de posiciones, permite comparar areas y mejora la interpretacion de patrones espaciales. Tambien sirve como base para analisis de cobertura, densidad o planificacion territorial.

### d) Como podria aplicarse este tipo de visualizacion en Ingenieria de Sistemas?

Puede aplicarse en:

- Analisis de cobertura de servicios digitales.
- Ubicacion de sensores IoT.
- Distribucion de usuarios de una plataforma.
- Diseno de rutas.
- Visualizacion de puntos de atencion.
- Analisis territorial para toma de decisiones.

Por ejemplo, una empresa podria usar una malla para decidir donde instalar antenas, centros de soporte, sensores ambientales o puntos de atencion.

## Respuestas a las preguntas de analisis

### 1. Por que es importante delimitar un dominio antes de construir una visualizacion espacial?

Porque permite definir con precision el area de estudio. Sin un dominio, la visualizacion puede incluir zonas innecesarias, perder escala o mostrar informacion desordenada. El dominio tambien permite generar correctamente cuadriculas y mallas dentro de limites claros.

### 2. Que informacion aporta el grafico de puntos reales?

Aporta la ubicacion exacta de ciudades o localidades del dataset. Permite observar concentraciones, dispersion territorial, zonas con alta presencia de registros y zonas con poca presencia de datos.

### 3. Que representa una cuadricula de puntos en visualizacion de datos?

Representa una division regular del espacio mediante puntos generados con una separacion constante. No son datos reales, sino referencias espaciales que ayudan a organizar el dominio geografico.

### 4. Que diferencia existe entre una cuadricula y una malla?

La cuadricula esta formada por puntos generados regularmente. La malla agrega lineas horizontales y verticales que conectan esos puntos, formando celdas visuales sobre el dominio.

### 5. Que ocurre visualmente si se reduce el valor de dx y dy?

La cuadricula se vuelve mas densa y aparecen mas puntos y lineas. Esto aumenta el detalle espacial, pero si los valores son demasiado pequenos la visualizacion puede verse saturada.

### 6. Que ocurre visualmente si se aumenta el valor de dx y dy?

La cuadricula se vuelve mas separada y aparecen menos puntos y lineas. Esto simplifica la visualizacion, pero reduce el nivel de detalle para analizar el dominio.

### 7. Como puede ayudar esta visualizacion en la toma de decisiones dentro de Ingenieria de Sistemas?

Ayuda a relacionar datos con ubicaciones reales. En Ingenieria de Sistemas puede apoyar decisiones sobre cobertura de internet, ubicacion de servidores o sensores, rutas de atencion, distribucion de usuarios, monitoreo territorial y planificacion de servicios digitales.

## Conclusion

La practica se cumple completamente porque la aplicacion implementa todo el flujo solicitado: carga y exploracion de datos, limpieza, seleccion de Peru, calculo del dominio, visualizacion de puntos reales, generacion de cuadricula, construccion de malla, interpretacion y descarga de informe PDF.

El modelado de dominios permite delimitar una region de analisis a partir de coordenadas espaciales. Las cuadriculas y mallas son recursos visuales utiles porque ordenan el territorio y facilitan la interpretacion de patrones geograficos para problemas de cobertura, movilidad, sensores, servicios digitales y toma de decisiones basada en datos.
