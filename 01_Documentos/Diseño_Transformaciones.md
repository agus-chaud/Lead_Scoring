# Diseño de Transformaciones — Lead Scoring

**Estado:** CONGELADO — aprobado por el usuario el 2026-09-16  
**Proyecto:** Lead Scoring  
**Fecha:** 2026-09-16  
**Objetivo:** clasificación binaria para estimar `compra`; priorizar recall, controlando precisión operativa.  
**Target:** `compra`  
**Modelos priorizados:** regresión logística por interpretabilidad; árboles quedan pendientes.

**Bloque categóricas:** APROBADO por el usuario el 2026-09-16.
**Bloque numéricas y fechas:** APROBADO por el usuario el 2026-09-16.
**Bloque texto, IDs y casos especiales:** APROBADO por el usuario el 2026-09-16.

## Matriz de transformaciones propuesta

| Variable | Tipo_Original | Transformación_1 | Tipo_Resultado_1 | Transformación_2 | Tipo_Resultado_2 | Escalado_Final | Es_Final | Incluir_DF | Nombre_Col_Final | Justificación |
|---|---|---|---|---|---|---|---|---|---|---|
| id | id/pseudo-id | Excluir | — | — | — | NO | NO | NO | — | Identificador único; conservar solo para trazabilidad. |
| origen | cat_nominal | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | origen_* | Cuatro categorías nominales. |
| fuente | cat_nominal | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | fuente_* | Cinco categorías ya consolidadas. |
| no_enviar_email | binaria | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | no_enviar_email_* | Señal binaria; no escalar. |
| no_llamar | binaria | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | no_llamar_* | Señal binaria; no escalar. |
| compra | binaria (target) | Sin transformación | binaria | — | — | NO | SÍ | SÍ | compra | Target de clasificación. |
| visitas_total | num_discreta | Yeo-Johnson | num_continua | MinMaxScaler | num_continua | MinMaxScaler | SÍ | SÍ | visitas_total_yj_mm | Asimetría positiva; salida en rango 0–1 para modelo lineal. |
| tiempo_en_site_total | num_discreta | Yeo-Johnson | num_continua | MinMaxScaler | num_continua | MinMaxScaler | SÍ | SÍ | tiempo_en_site_total_yj_mm | Asimetría positiva; salida en rango 0–1 para modelo lineal. |
| paginas_vistas_visita | num_continua | Yeo-Johnson | num_continua | MinMaxScaler | num_continua | MinMaxScaler | SÍ | SÍ | paginas_vistas_visita_yj_mm | Asimetría positiva; salida en rango 0–1 para modelo lineal. |
| ult_actividad | cat_nominal | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | ult_actividad_* | Ocho categorías tras agrupar raras. |
| ambito | cat_nominal | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | ambito_* | Veinte categorías, sin alta cardinalidad. |
| ocupacion | cat_nominal | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | ocupacion_* | Siete categorías; `Desconocido` es informativo. |
| conociste_google | binaria | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | conociste_google_* | Señal binaria; no escalar. |
| conociste_revista | constante | Excluir | — | — | — | NO | NO | NO | — | Sin variación predictiva. |
| conociste_periodico | constante | Excluir | — | — | — | NO | NO | NO | — | Sin variación predictiva. |
| conociste_youtube | constante | Excluir | — | — | — | NO | NO | NO | — | Sin variación predictiva. |
| conociste_facebook | binaria | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | conociste_facebook_* | Señal binaria; no escalar. |
| conociste_referencias | binaria | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | conociste_referencias_* | Señal binaria; no escalar. |
| score_actividad | num_discreta | SimpleImputer(mediana) + indicador | num_continua + binaria | MinMaxScaler (solo valor) | num_continua | MinMaxScaler | SÍ | SÍ | score_actividad_mm, score_actividad_missing | Los NaN son estructurales y su indicador debe preservarse; el valor queda en rango 0–1. |
| score_perfil | num_discreta | SimpleImputer(mediana) | num_continua | MinMaxScaler | num_continua | MinMaxScaler | SÍ | SÍ | score_perfil_mm | Su ausencia coincide exactamente con la de `score_actividad`; se representa una sola vez. |
| descarga_lm | binaria | OneHotEncoder(drop="first") | binaria | — | — | NO | SÍ | SÍ | descarga_lm_* | Señal binaria; no escalar. |
| visitas_total_missing | binaria | Sin transformación | binaria | — | — | NO | SÍ | SÍ | visitas_total_missing | Indicador existente de ausencia; no escalar. |
| paginas_vistas_visita_missing | binaria | Excluir | — | — | — | NO | NO | NO | — | Es idéntico a `visitas_total_missing`; se conserva una sola señal. |

## Decisiones tomadas

- `DEC-006` — Estrategia consolidada de feature engineering.

## Riesgos identificados

- Las dummies incrementarán dimensionalidad, especialmente `ambito`; es aceptable para regresión logística dada su cardinalidad moderada.
- Los indicadores de ausencia de scores deben acompañar a la imputación para conservar su señal de negocio.
- Las transformaciones numéricas propuestas deben producir solamente la versión final escalada; no se conservarán originales ni intermedias.
- Los pares de indicadores duplicados se reducen a una sola señal para evitar multicolinealidad perfecta.
- La matriz sigue en negociación: ninguna de estas transformaciones fue aplicada a `df`.
