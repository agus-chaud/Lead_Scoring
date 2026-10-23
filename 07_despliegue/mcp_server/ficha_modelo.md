# Ficha del modelo de scoring de leads

## Qué es

Un modelo que estima la **probabilidad de que un lead termine comprando**. Sirve para decidir a quién contactar primero. Ordena a los leads; no garantiza que uno compre ni explica por qué compraría.

## Con qué datos trabaja

- **Entrada:** 12 datos del lead: origen, fuente, si aceptó emails, visitas totales, tiempo en el sitio, páginas vistas por visita, última actividad, ámbito, ocupación, los dos scores de marketing automation y si descargó el material.
- **Datos de aprendizaje:** 6.360 leads históricos (el 70% del total), de los cuales el 37,5% compró. El 30% restante se reservó para validar y el modelo nunca lo vio al aprender.
- **Rechazo de extremos:** un lead con más de 30 visitas o más de 20 páginas por visita se rechaza, porque se consideraron valores atípicos (posibles bots).

## Cómo calcula el resultado

Es una **regresión logística con splines**. Cada dato del lead suma o resta "puntos" a favor de la compra. El modelo combina todos esos puntos y los convierte en una probabilidad entre 0 y 1 (el `score`). Si el score llega a 0,5, la `prediccion` es 1.

En los 4 datos numéricos continuos (tiempo en el sitio, páginas vistas por visita y los dos scores de marketing automation), los puntos no crecen en línea recta: siguen una curva suave (splines), que puede subir, frenarse o bajar según el tramo del valor. Por ejemplo, pasar de 0 a algunos segundos en el sitio no pesa lo mismo que pasar de mucho a muchísimo tiempo. El resto de los datos funciona igual que en una regresión logística común.

Configuración actual: penalización L2, C = 1,22, splines cúbicos con 6 nodos. Parte de 40 columnas derivadas de los 12 datos (cada categoría de un dato pasa a ser una columna), elegidas en la preselección de variables; cada numérica continua se expande en 8 columnas de curva, así que el modelo trabaja con 68 columnas. Los datos faltantes se rellenan antes de calcular y, en visitas y en el score de actividad, el modelo además sabe que estaban vacíos.

## Qué tan bien funciona

Medido una sola vez sobre 2.722 leads que el modelo nunca vio (el 30% reservado para validar):

- **Capacidad de ordenar (AUC): 0,910.** Si tomás un lead que compró y uno que no, el modelo le da más score al comprador el 91,0% de las veces. Durante el desarrollo, con validación cruzada, había dado 0,911: los dos números son consistentes.
- **Si se prioriza por score:** entre el 10% de leads con más score compra el 97% y se capturan el 26% de todos los compradores. En el 20% superior compra el 92% (48% de los compradores). En el 30% superior compra el 85% (67% de los compradores). Sin modelo, compra el 37,9%.
- **Con el corte en 0,5:** acierta 84 de cada 100 leads. De cada 100 que marca como compradores, 81 compran (precisión). De cada 100 compradores reales, detecta 76 (recall).
- **Contra el modelo anterior** (regresión logística sin splines), sobre los mismos leads: el AUC sube de 0,887 a 0,910 y el recall de 71 a 76 de cada 100 compradores.

El modelo desplegado se entrenó solo con el 70% de los datos, así que estas cifras no están contaminadas por haber visto los leads evaluados.

## Por qué usa splines y cómo comprobamos que es mejor

**El problema de la regresión logística tradicional.** La versión tradicional supone que cada dato numérico empuja la probabilidad de compra siempre igual: si 5 minutos más en el sitio suman, otros 5 minutos suman exactamente lo mismo, sin importar si el lead estuvo 1 minuto o 1 hora. Es como medir una ruta con una regla recta: sirve si el camino es recto, pero falla en las curvas.

**Qué son los splines.** Un spline es una forma de dibujar una curva suave uniendo varios tramos. El modelo parte cada dato numérico en tramos (acá, separados por 6 puntos llamados "nodos") y en cada tramo ajusta una curva. Así puede aprender, por ejemplo, que pasar de 0 a unos minutos en el sitio sube mucho las chances y que, después de cierto punto, más tiempo ya casi no agrega. Los datos que no son números (como la ocupación o la fuente) siguen igual.

**Por qué no pierde explicabilidad.** Aunque las curvas sean más flexibles, el modelo sigue armando el resultado sumando el aporte de cada dato por separado. Por eso `explain_score` puede mostrar, con exactitud y sin aproximaciones, cuánto sube o baja cada dato el score de un lead.

**Cómo comprobamos que de verdad es mejor.** Usamos dos pruebas, las dos con leads que el modelo no había visto al aprender:

- **Validación cruzada.** Durante el desarrollo, los datos de entrenamiento se dividieron en 5 partes ("folds"). El modelo aprendió con 4 partes y se evaluó con la quinta, y eso se repitió 5 veces rotando la parte de evaluación. Los dos modelos usaron exactamente las mismas 5 divisiones, así que la comparación es justa. Con splines el AUC promedio pasó de 0,892 a 0,911, y fue mejor en las 5 rondas, no solo en promedio.
- **Validación externa (`validation.pkl`).** Antes de empezar se apartó el 30% de los leads y nadie lo usó para elegir ni ajustar el modelo. Recién al final se evaluaron ahí los dos modelos, una sola vez: el AUC pasó de 0,887 a 0,910. Es la prueba más parecida a usar el modelo con leads nuevos.
- **¿Puede ser suerte?** Para descartarlo usamos **bootstrap**: se armaron 1.000 muestras al azar a partir de los leads de validación y en cada una se volvió a comparar a los dos modelos. Los splines ganaron en las 1.000. En el 95% de los casos la mejora de AUC quedó entre 0,017 y 0,028, siempre por encima de cero.

## Qué señales pesan más

Según el análisis exploratorio, separan mejor a compradores de no compradores la **ocupación**, la **última actividad**, el **origen** del lead, el **ámbito** y la **fuente**, y entre las numéricas el **tiempo en el sitio**. Para ver cómo influye cada dato en un lead concreto, usá la herramienta `explain_score`.

## Límites y advertencias

- **Posible leakage.** El rendimiento del modelo depende bastante de `ult_actividad` y `ocupacion`, y no se descarta que reflejen información posterior al contacto comercial (DEC-014). En la auditoría (validación cruzada, hecha con el modelo sin splines) el AUC pasaba de 0,895 a 0,838 al quitar ambas. Si el lead se puntúa antes de que esas variables existan, el score real será menos preciso.
- **Es correlación, no causa.** Que una variable suba el score no significa que cambiarla haga comprar a ese lead.
- **Faltantes frecuentes.** Los scores de marketing automation faltan en el 46% de los leads (suelen ser leads nuevos), y la ocupación en el 30%. Con muchos datos vacíos el score es menos confiable.
- **Campos que nunca faltaron al entrenar.** Origen, aceptación de emails y descarga del material siempre venían completos. Si llegan vacíos, el modelo los trata como la categoría de referencia (origen API o Lead Add Form, que codifican igual; "No" en los otros dos), y el tiempo en el sitio vacío se reemplaza por la mediana. El resultado en esos casos es una estimación sin respaldo en los datos de entrenamiento.
- **El corte 0,5 no está calibrado con evidencia de negocio.** Es un valor convencional. Todavía no se midió qué corte conviene según costo y beneficio del contacto comercial.
- **Las curvas no se extienden más allá de lo visto.** Fuera del rango de valores de entrenamiento, el aporte de un dato numérico queda fijo en el del borde de la curva. Además, algunas formas de la curva pueden no ser intuitivas: por ejemplo, 0 páginas vistas por visita sube el score respecto de un lead típico. Refleja un patrón de los datos históricos, no una regla de negocio.
- **Categorías muy raras son inestables.** Por ejemplo, `Housewife` tiene pocos casos (DEC-015 propone agruparlas y sigue pendiente).
- **Datos de un solo origen.** El modelo aprendió de un único conjunto histórico; si cambia el perfil de los leads, hay que revisarlo y reentrenarlo.

## Historial

Hasta el 22/10/2026 la API ejecutaba un modelo distinto del que describían los notebooks (más columnas, entrenado con todos los leads y sin validación externa). Desde la alineación (DEC-016), el modelo desplegado es el de los notebooks. El 22/10/2026 la regresión logística lineal (C = 14,53, AUC 0,887 en validación) se reemplazó por la versión con splines (DEC-019).
