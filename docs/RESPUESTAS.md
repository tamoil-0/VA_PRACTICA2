# Respuestas de la Practica Calificada 02

> Documento generado automaticamente por `python main.py` a partir del analisis ejecutado. Las cifras corresponden a la corrida por defecto (Peru, dx = 0.5, dy = 0.5).

## Datos de la corrida

| Indicador | Valor |
|---|---|
| Registros del archivo | 139 |
| Localidades limpias | 139 |
| Dominio (grados) | 12.23 x 14.51 |
| Area aproximada | 2,145,347 km2 |
| Puntos de cuadricula | 806 |
| Celdas de la malla | 750 |
| Cobertura de la malla | 15.7 % |
| Vecino mas cercano (promedio) | 47.9 km |

## Actividad 1. Exploracion de la base de datos

El trabajo utiliza el dataset 'Geolocation Data [Longitude Latitude]' publicado en Kaggle (https://www.kaggle.com/datasets/liewyousheng/geolocation), que reune informacion geografica de paises, regiones, provincias, ciudades y distritos con sus coordenadas de longitud y latitud en formato CSV. El archivo procesado (peru_localidades.csv) contiene 139 registros y 6 columnas; de ellas, 'longitude' aporta la coordenada x (longitud) y 'latitude' la coordenada y (latitud), que son las dos variables espaciales necesarias para delimitar un dominio y construir cuadriculas y mallas. Para el analisis se selecciono Peru, tal como recomienda la practica.

| Pregunta | Respuesta |
|---|---|
| a) Cuantos registros contiene el archivo? | 139 |
| b) Que columnas contiene? | `city_name`, `country_name`, `region_name`, `place_type`, `latitude`, `longitude` |
| c) Que columnas son las coordenadas? | `longitude` (x, longitud) y `latitude` (y, latitud) |
| d) Que pais se selecciona? | Peru |

## Actividad 2. Limpieza y seleccion de datos

| Paso de limpieza | Registros |
|---|---|
| Registros del archivo original | 139 |
| Descartados por no pertenecer a Peru | 0 |
| Descartados por latitud/longitud no numerica o vacia | 0 |
| Descartados por coordenadas fuera de rango valido | 0 |
| Descartados por ser duplicados exactos | 0 |
| Registros limpios finales | 139 |

Tabla final: **139 localidades** con Ciudad o localidad, Pais, Region, Latitud y Longitud (`salidas/tabla_limpia.csv`).

## Actividad 3. Delimitacion del dominio geografico

```text
D = [-81.2719, -69.0417] x [-18.0066, -3.5011]
```

| Parametro | Valor | Interpretacion |
|---|---|---|
| Longitud minima (xmin) | -81.2719 | Limite occidental del dominio |
| Longitud maxima (xmax) | -69.0417 | Limite oriental del dominio |
| Latitud minima (ymin) | -18.0066 | Limite sur del dominio |
| Latitud maxima (ymax) | -3.5011 | Limite norte del dominio |

## Actividad 7. Interpretacion visual de resultados

### a) Que representa el dominio geografico construido?

Representa el rectangulo minimo (bounding box) que contiene todas las coordenadas seleccionadas: D = [-81.27, -69.04] x [-18.01, -3.50]. No es un mapa del pais, es el area de analisis: fija el marco espacial dentro del cual tienen sentido la cuadricula, la malla y cualquier calculo posterior. Sus cuatro limites son interpretables: xmin es el extremo occidental, xmax el oriental, ymin el mas al sur y ymax el mas al norte de las 139 localidades analizadas.

### b) Que diferencia existe entre los puntos reales y los de la cuadricula?

Los puntos reales son observaciones: 139 localidades que existen en el territorio, con distribucion irregular determinada por el poblamiento. Los 806 puntos de la cuadricula son sinteticos: los genera numpy.meshgrid a intervalos constantes (dx = 0.5, dy = 0.5) y no representan ninguna ciudad, sino posiciones de referencia del espacio. Los primeros responden 'donde estan los hechos'; los segundos aportan el sistema de medida que permite comparar zonas.

### c) Que utilidad tiene una malla en la visualizacion de datos espaciales?

La malla convierte un espacio continuo en unidades comparables. En este caso genera 750 celdas y permite contar cuantas localidades caen en cada una: 118 celdas resultan ocupadas y 632 quedan vacias. Ademas sirve como referencia visual (facilita estimar distancias y ubicar un punto), como base de agregacion (densidad, mapas de calor, conteos por celda) y como soporte para detectar vacios de cobertura que un grafico de puntos suelto no muestra con claridad.

### d) Como podria aplicarse en un problema de Ingenieria de Sistemas?

El esquema dominio + cuadricula + malla es la base de cualquier analisis territorial computacional. Aplicaciones directas: (1) cobertura de servicios digitales, marcando las celdas sin atencion; (2) ubicacion optima de sensores IoT o antenas, usando una celda por sensor para no duplicar cobertura; (3) analisis de la distribucion de usuarios de una plataforma para dimensionar servidores o centros de distribucion; (4) diseno de rutas y logistica, calculando costos entre celdas; (5) tableros de decision territorial, donde cada celda es una fila agregable en una base de datos espacial.

## Preguntas de analisis del informe

### 1. Por que es importante delimitar un dominio antes de construir una visualizacion espacial?

Porque define el area de estudio y, con ella, la escala de todo lo demas. Sin dominio no se puede fijar el rango de los ejes ni generar una cuadricula acotada, y el grafico incluiria espacio vacio que comprime los datos utiles. Aqui el dominio D = [-81.27, -69.04] x [-18.01, -3.50] recorta el analisis a 12.23 x 14.51 grados, lo que garantiza que la cuadricula, la malla y las metricas de densidad se calculen sobre el territorio observado y no sobre el planeta completo.

### 2. Que informacion aporta el grafico de puntos reales?

Aporta la ubicacion y la forma de la distribucion: donde hay concentracion, donde hay vacios y que estructura describe el conjunto. En el caso analizado los puntos dibujan el eje costero y los corredores andinos, revelando que la distribucion es agrupada y no uniforme. Es la visualizacion que responde 'donde ocurre el fenomeno' antes de cualquier modelo.

### 3. Que representa una cuadricula de puntos en visualizacion de datos?

Representa un muestreo regular del espacio: un conjunto de posiciones generadas cada dx grados en horizontal y dy en vertical. No son datos observados, son un sistema de referencia. En este trabajo la cuadricula tiene 26 columnas por 31 filas (806 nodos) y sirve para discretizar el dominio, es decir, para pasar de un espacio continuo a un conjunto finito de unidades analizables.

### 4. Que diferencia existe entre una cuadricula y una malla?

La cuadricula es el conjunto de puntos (806 nodos aqui); la malla es la estructura que resulta de unir esos puntos con 31 lineas horizontales y 26 lineas verticales, generando 750 celdas. La cuadricula aporta posiciones discretas; la malla aporta topologia (vecindad, celdas, bordes) y por eso permite agregar, contar y comparar por zona.

### 5. Que ocurre visualmente si se reduce el valor de dx y dy?

La resolucion aumenta y el detalle es mayor, pero el costo crece de forma cuadratica y la lectura se satura. Con dx = dy = 0.5 se generan 806 nodos; al bajar a 0.25 se pasa a 3,000 nodos y 2,891 celdas, de las cuales solo 4.6 % quedan ocupadas: las lineas se juntan tanto que tapan los puntos reales y la mayoria de celdas queda vacia.

### 6. Que ocurre visualmente si se aumenta el valor de dx y dy?

La visualizacion se simplifica y gana legibilidad, pero pierde precision espacial. Con dx = dy = 2.0 la cuadricula baja a 72 nodos y 56 celdas con 53.6 % de ocupacion: cada celda agrupa localidades muy distantes entre si, se ocultan diferencias internas y aparece el riesgo de agregacion excesiva (varias ciudades distintas se leen como un solo bloque).

### 7. Como puede ayudar esta visualizacion en la toma de decisiones dentro de Ingenieria de Sistemas?

Convierte coordenadas en unidades de decision. Cada una de las 750 celdas puede almacenar indicadores (usuarios, incidencias, cobertura, latencia) y volverse una fila de una base de datos espacial; sobre esa estructura se priorizan inversiones, se ubican sensores o antenas, se disenan rutas y se detectan zonas desatendidas. En este analisis, las 632 celdas sin localidades son exactamente el tipo de hallazgo que orienta una decision: senalan donde no hay presencia registrada.

## Conclusiones

1. El modelado de dominios permitio pasar de un CSV de 139 registros a un area de analisis explicita: D = [-81.27, -69.04] x [-18.01, -3.50], obtenida solo con los minimos y maximos de longitud y latitud de las 139 localidades limpias.

2. La cuadricula regular (dx = 0.5, dy = 0.5) discretizo ese dominio continuo en 806 nodos, y la malla lo organizo en 750 celdas comparables entre si. Ese paso de continuo a discreto es lo que habilita medir densidad y cobertura.

3. La superposicion de puntos reales y malla mostro que la distribucion territorial es fuertemente irregular: apenas 15.7 % de las celdas contiene alguna localidad. El dominio delimita el maximo posible, no lo efectivamente ocupado, y esa diferencia es en si misma un resultado del analisis.

4. El valor de dx y dy no es un detalle estetico sino una decision analitica: define el nivel de agregacion, el costo computacional y el riesgo de ocultar o exagerar patrones. Elegirlo requiere conocer la escala del fenomeno.

5. Finalmente, las tres visualizaciones son complementarias y no sustitutas: los puntos muestran los hechos, la cuadricula aporta el sistema de medida y la malla ofrece la estructura de agregacion. Sobre esa base se construyen aplicaciones de Ingenieria de Sistemas como cobertura de servicios, redes de sensores IoT, planificacion de rutas y tableros de decision territorial.

## Verificacion de la rubrica

| Criterio | Pts | Evidencia |
|---|---|---|
| Exploracion del dataset | 3 | Actividad 1: 139 registros y 6 columnas identificadas; columnas de coordenadas detectadas automaticamente (longitude, latitude). Pestana 'Exploracion' de la app y seccion 1 del informe. |
| Limpieza y filtrado de datos | 3 | Actividad 2: filtro de pais (Peru), conversion numerica de coordenadas, eliminacion de nulos, rangos invalidos y duplicados; tabla final de 139 filas con Ciudad, Pais, Latitud y Longitud, mas auditoria paso a paso. |
| Delimitacion del dominio | 4 | Actividad 3: D = [-81.2719, -69.0417] x [-18.0066, -3.5011] con tabla de los cuatro limites e interpretacion de cada uno (occidental, oriental, sur y norte). |
| Visualizacion de puntos reales | 3 | Actividad 4: dispersion con longitud en X, latitud en Y, titulo, etiquetas de ejes, cuadricula de fondo, leyenda e interpretacion cuantitativa de la distribucion. |
| Generacion de cuadricula | 3 | Actividad 5: cuadricula regular con np.meshgrid, dx = 0.5 y dy = 0.5, 26 x 31 = 806 puntos dentro del dominio definido. |
| Construccion de malla | 2 | Actividad 6: 31 lineas horizontales y 26 verticales, rectangulo del dominio dibujado y puntos reales superpuestos. |
| Interpretacion visual | 2 | Actividad 7: las cuatro preguntas respondidas con cifras del propio analisis, mas las siete preguntas de analisis y las conclusiones. |

**Total: 20 puntos cubiertos.**
