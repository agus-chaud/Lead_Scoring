# Alinear producción con los notebooks (camino A)
Objetivo: que `01_reentrenamiento.py`, la API y el MCP produzcan el modelo del contrato `00_manifiesto_preproduccion.json`, no el modelo B.
Rama: feat/alinear-produccion-notebooks | Entrega: ask-on-risk (sin push sin pedido) | Runner: pytest en venv con `07_despliegue/api/requirements.txt` + `mcp_server/requirements.txt`

## Specs
- S1. Split `train_test_split(leads, test_size=0.30, random_state=42)` sin estratificar (P02). El modelo se entrena SOLO con `df_train` (tras filtrar extremos); ningún id de `validation.pkl` entra al entrenamiento.
- S2. Ruta de inferencia = contrato: calidad y reglas de categorías (P03/P04: `transformaciones.json` y `01_reglas_categorias.json`) → `05_modelos/preprocesador.joblib` congelado (P05) → las 40 variables de `01_Documentos/Variables_preseleccionadas.txt` en ese orden (P06/P07) → `LogisticRegression(C=14.528246637516036, penalty="l2", solver="saga", max_iter=5000, random_state=42)` (P08, `config_mejor_modelo.json`).
- S3. Sin búsqueda de hiperparámetros en producción: DEC-012 queda reemplazada.
- S4. Misma interfaz del artefacto: `predict_proba` sobre filas crudas; el contrato de `POST /predict` (`id`, `score`, `prediccion`) no cambia.
- S5. `/explain` y `explain_score` siguen descomponiendo el logit de forma exacta por variable original; la referencia (lead promedio) se regenera para el modelo nuevo.
- S6. Evaluar UNA vez sobre `validation.pkl`, registrar las métricas, y no ajustar nada después de verlas.
- S7. Documentación coherente con un solo camino: README, ficha del modelo y nueva DEC-016 (reemplaza DEC-012, aclara DEC-010).
- Supuestos (no pedidos por el usuario): (a) las columnas que la API no recibe (`no_llamar`, `conociste_*`) se completan con "No" porque el preprocesador congelado las exige; (b) constantes de imputación 3,0 y 2,0 tomadas de `transformaciones.json`; (a') en `origen`, `no_enviar_email` y `descarga_lm` un faltante se codifica "Desconocido" (ceros, igual que la categoría de referencia) porque el codificador congelado nunca vio NaN; (a'') `tiempo_en_site_total` faltante se imputa con la mediana de train (no tenía imputador y nunca faltó); (c) el entrenamiento usa el 70%, como dice el contrato, sin reajustar luego con el 100%.

## Tasks
- [x] T1 (S1,S2,S3,S4) Reescribir `01_reentrenamiento.py` según el contrato + test de paridad con el notebook 08 | inline | 6 tests verdes (RED observado antes: el script viejo no exponía `entrenar`) | commit: ver git log (feat(produccion))
- [ ] T2 (S5) Adaptar `/explain` a los nombres canónicos, regenerar referencia, tests de API | inline | commit: -
- [ ] T3 (S6) Evaluar una vez sobre validation.pkl; adaptar `02_produccion_scoring.py` | inline | commit: -
- [ ] T4 (S7) README, ficha, DEC-016, tests de coherencia de la ficha | inline | commit: -

## Log
- L1 (2026-10-22, usuario): "Que producción siga a los notebooks (A)"
- L0 (2026-10-22, usuario, contexto): "quiero alinear los 2 caminos"
- Hallazgos de exploración: el split reproduce validation.pkl (2.728 filas, 0 solape con las 6.365 de train); el preprocesador congelado exige columnas que la API no recibe; la salida del ColumnTransformer puede ser esparsa (sparse_threshold 0,3).
- Route declaration: todo inline; ningún Writer trigger aplica (unidades dependientes entre sí).
- Hallazgo T1: la paridad inicial falló por un error del test (alimenté filas ya limpiadas, recalculó los flags de faltantes); coeficientes idénticos al notebook (diferencia 0,0).
