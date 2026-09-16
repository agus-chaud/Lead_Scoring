# Informe de transformación — Lead Scoring

## Resumen

- Input: `02_datos/03_Entrenamiento/03_train_tablon_eda.pkl`
- Output: `02_datos/03_Entrenamiento/04_train_tablon_transformado.pkl`
- Filas: 6360
- Columnas finales: 53
- Problema: clasificación binaria; target `compra`.
- Objetivo: priorizar recall, controlando precisión operativa.
- Modelo priorizado: regresión logística interpretable.

## Transformaciones

- Categóricas y binarias objeto: `OneHotEncoder(drop="first")`, sin escalado.
- Comportamiento: Yeo-Johnson y MinMaxScaler; finales `visitas_total, tiempo_en_site_total, paginas_vistas_visita` con sufijo `_yj_mm`.
- Scores: mediana, indicador estructural de ausencia y MinMaxScaler para el valor; finales `score_actividad_mm`, `score_perfil_mm`, `score_actividad_missing`.
- IDs y constantes: `id`, `conociste_revista`, `conociste_periodico` y `conociste_youtube` excluidos.

## Gestión de versiones intermedias

Los originales categóricos y numéricos transformados, junto con cualquier versión intermedia, fueron excluidos. Solo se conserva `compra`, las versiones finales y los indicadores binarios aprobados.

## Validaciones realizadas

- filas_preservadas: OK
- target_presente: OK
- sin_columnas_intermedias: OK
- sin_originales_transformados: OK
- sin_nan_inesperados: OK
- nombres_unicos: OK
- sin_multicolinealidad_binaria_perfecta: OK

## Reproducibilidad

El preprocesador ajustado exclusivamente sobre el tablón de entrenamiento se guardó en `05_modelos/preprocesador.joblib`. Su `transform(X_raw)` reproduce las 52 columnas predictoras finales.
