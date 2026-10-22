# Ficha del modelo de scoring de leads

## Qué es

Un modelo que estima la **probabilidad de que un lead termine comprando**. Sirve para decidir a quién contactar primero. Ordena a los leads; no garantiza que uno compre ni explica por qué compraría.

## Con qué datos trabaja

- **Entrada:** 12 datos del lead: origen, fuente, si aceptó emails, visitas totales, tiempo en el sitio, páginas vistas por visita, última actividad, ámbito, ocupación, los dos scores de marketing automation y si descargó el material.
- **Datos de aprendizaje:** 6.360 leads históricos (el 70% del total), de los cuales el 37,5% compró. El 30% restante se reservó para validar y el modelo nunca lo vio al aprender.
- **Rechazo de extremos:** un lead con más de 30 visitas o más de 20 páginas por visita se rechaza, porque se consideraron valores atípicos (posibles bots).

## Cómo calcula el resultado

Es una **regresión logística**, la más simple y transparente de las familias de modelos. Cada dato del lead suma o resta "puntos" a favor de la compra. El modelo combina todos esos puntos y los convierte en una probabilidad entre 0 y 1 (el `score`). Si el score llega a 0,5, la `prediccion` es 1.

Configuración actual: penalización L2, C = 14,53. Trabaja con 40 columnas derivadas de los 12 datos (cada categoría de un dato pasa a ser una columna), elegidas en la preselección de variables. Los datos faltantes se rellenan antes de calcular y, en visitas y en el score de actividad, el modelo además sabe que estaban vacíos.

## Qué tan bien funciona

Medido una sola vez sobre 2.722 leads que el modelo nunca vio (el 30% reservado para validar):

- **Capacidad de ordenar (AUC): 0,887.** Si tomás un lead que compró y uno que no, el modelo le da más score al comprador el 88,7% de las veces. Durante el desarrollo, con validación cruzada, había dado 0,892: los dos números son consistentes.
- **Si se prioriza por score:** entre el 10% de leads con más score compra el 94% y se capturan el 25% de todos los compradores. En el 20% superior compra el 89% (47% de los compradores). En el 30% superior compra el 81% (64% de los compradores). Sin modelo, compra el 37,9%.
- **Con el corte en 0,5:** acierta 81 de cada 100 leads. De cada 100 que marca como compradores, 78 compran (precisión). De cada 100 compradores reales, detecta 71 (recall).

El modelo desplegado se entrenó solo con el 70% de los datos, así que estas cifras no están contaminadas por haber visto los leads evaluados.

## Qué señales pesan más

Según el análisis exploratorio, separan mejor a compradores de no compradores la **ocupación**, la **última actividad**, el **origen** del lead, el **ámbito** y la **fuente**, y entre las numéricas el **tiempo en el sitio**. Para ver cómo influye cada dato en un lead concreto, usá la herramienta `explain_score`.

## Límites y advertencias

- **Posible leakage.** El rendimiento del modelo depende bastante de `ult_actividad` y `ocupacion`, y no se descarta que reflejen información posterior al contacto comercial (DEC-014). En la auditoría (validación cruzada) el AUC pasaba de 0,895 a 0,838 al quitar ambas. Si el lead se puntúa antes de que esas variables existan, el score real será menos preciso.
- **Es correlación, no causa.** Que una variable suba el score no significa que cambiarla haga comprar a ese lead.
- **Faltantes frecuentes.** Los scores de marketing automation faltan en el 46% de los leads (suelen ser leads nuevos), y la ocupación en el 30%. Con muchos datos vacíos el score es menos confiable.
- **Campos que nunca faltaron al entrenar.** Origen, aceptación de emails y descarga del material siempre venían completos. Si llegan vacíos, el modelo los trata como la categoría de referencia (origen API o Lead Add Form, que codifican igual; "No" en los otros dos), y el tiempo en el sitio vacío se reemplaza por la mediana. El resultado en esos casos es una estimación sin respaldo en los datos de entrenamiento.
- **El corte 0,5 no está calibrado con evidencia de negocio.** Es un valor convencional. Todavía no se midió qué corte conviene según costo y beneficio del contacto comercial.
- **Categorías muy raras son inestables.** Por ejemplo, `Housewife` tiene pocos casos (DEC-015 propone agruparlas y sigue pendiente).
- **Datos de un solo origen.** El modelo aprendió de un único conjunto histórico; si cambia el perfil de los leads, hay que revisarlo y reentrenarlo.

## Historial

Hasta el 22/10/2026 la API ejecutaba un modelo distinto del que describían los notebooks (más columnas, entrenado con todos los leads y sin validación externa). Desde la alineación (DEC-016), el modelo desplegado es el de los notebooks.
