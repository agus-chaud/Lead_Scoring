# Ficha del modelo de scoring de leads

## Qué es

Un modelo que estima la **probabilidad de que un lead termine comprando**. Sirve para decidir a quién contactar primero. Ordena a los leads; no garantiza que uno compre ni explica por qué compraría.

## Con qué datos trabaja

- **Entrada:** 12 datos del lead: origen, fuente, si aceptó emails, visitas totales, tiempo en el sitio, páginas vistas por visita, última actividad, ámbito, ocupación, los dos scores de marketing automation y si descargó el material.
- **Datos de aprendizaje:** 9.082 leads históricos, de los cuales el 37,6% compró.
- **Rechazo de extremos:** un lead con más de 30 visitas o más de 20 páginas por visita se rechaza, porque se consideraron valores atípicos (posibles bots).

## Cómo calcula el resultado

Es una **regresión logística**, la más simple y transparente de las familias de modelos. Cada dato del lead suma o resta "puntos" a favor de la compra. El modelo combina todos esos puntos y los convierte en una probabilidad entre 0 y 1 (el `score`). Si el score llega a 0,5, la `prediccion` es 1.

Configuración actual: penalización L1, C = 1,35. Trabaja con 59 columnas derivadas de los 12 datos (cada categoría de un dato pasa a ser una columna). Los datos faltantes se rellenan con un valor neutro y, en visitas y en el score de actividad, el modelo además sabe que estaban vacíos.

## Qué tan bien funciona

Medido con validación cruzada de 5 grupos sobre los 9.082 leads (cada lead se puntúa sin que el modelo lo haya visto al aprender):

- **Capacidad de ordenar (AUC): 0,895.** Si tomás un lead que compró y uno que no, el modelo le da más score al comprador el 89,5% de las veces. Entre grupos varió de 0,891 a 0,904.
- **Si se prioriza por score:** entre el 10% de leads con más score compra el 95% y se capturan el 25% de todos los compradores. En el 20% superior compra el 89% (48% de los compradores). En el 30% superior compra el 82% (65% de los compradores). Sin modelo, compra el 37,6%.
- **Con el corte en 0,5:** acierta 82 de cada 100 leads. De cada 100 que marca como compradores, 78 compran (precisión). De cada 100 compradores reales, detecta 72 (recall).

Estos números salen de una validación interna: el modelo desplegado se entrenó con todos los leads y no tiene un conjunto de validación externo limpio. Además, sus parámetros se eligieron sobre esos mismos datos, así que el desempeño en leads nuevos puede ser algo menor.

## Qué señales pesan más

Según el análisis exploratorio, separan mejor a compradores de no compradores la **ocupación**, la **última actividad**, el **origen** del lead, el **ámbito** y la **fuente**, y entre las numéricas el **tiempo en el sitio**. Para ver cómo influye cada dato en un lead concreto, usá la herramienta `explain_score`.

## Límites y advertencias

- **Posible leakage.** `ult_actividad` y `ocupacion` son las variables más influyentes y no se descarta que reflejen información posterior al contacto comercial (DEC-014). En un análisis del modelo candidato del proyecto, el AUC pasaba de 0,895 a 0,838 al quitar ambas. Si el lead se puntúa antes de que esas variables existan, el score real será menos preciso.
- **Es correlación, no causa.** Que una variable suba el score no significa que cambiarla haga comprar a ese lead.
- **Faltantes frecuentes.** Los scores de marketing automation faltan en el 46% de los leads (suelen ser leads nuevos), y la ocupación en el 30%. Con muchos datos vacíos el score es menos confiable.
- **El corte 0,5 no está calibrado con evidencia de negocio.** Es un valor convencional. Todavía no se midió qué corte conviene según costo y beneficio del contacto comercial.
- **Categorías muy raras son inestables.** Por ejemplo, `Housewife` tiene pocos casos (DEC-015 propone agruparlas y sigue pendiente).
- **Datos de un solo origen.** El modelo aprendió de un único conjunto histórico; si cambia el perfil de los leads, hay que revisarlo y reentrenarlo.

## Para quien audite la documentación del proyecto

El README y varias decisiones (DEC-007, DEC-009, DEC-010, DEC-012) describen un modelo candidato de 40 variables, penalización L2, C = 14,53 y AUC de 0,8919. **El modelo que hoy está desplegado es otro:** lo generó `01_reentrenamiento.py` con 12 datos de entrada (59 columnas), sin selección RFECV, penalización L1, C = 1,35, y se entrenó con todos los leads, no con el 70% de entrenamiento. Las cifras de esta ficha se midieron sobre ese modelo desplegado.
