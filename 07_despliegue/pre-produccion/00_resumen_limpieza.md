# Resumen de consolidación de preproducción

## Fase 0 — mapa y fases detectadas

- Raíz confirmada: `Lead_Scoring`.
- Fuente cruda confirmada mediante análisis estático de `03_notebooks/01_Importacion_Datos.ipynb`: `02_datos/01_Originales/Leads.csv`, con `sep=";"` y `encoding="utf-8"`.
- Están presentes los tablones intermedios `01` a `05`, el preprocesador ajustado, la lista de 40 variables finalistas y la configuración del modelo candidato.
- Fases detectadas: importación, separación train/validación, calidad, EDA, transformación, preselección y modelización logística. No se detectó artefacto de balanceo: no se incorpora balanceo.

## Fase 1 — integración pendiente de revisión

- Se creó `03_notebooks/08_Preproduccion.ipynb` sin ejecutarlo.
- Se integraron: lectura real del CSV, split 70/30 con `random_state=42`, calidad, consolidación de categorías del EDA, carga del preprocesador ajustado, selección de las 40 finalistas y ajuste de `LogisticRegression` con la configuración congelada.
- Se usa el artefacto `05_modelos/preprocesador.joblib`; no se reconstruye `Pipeline` ni `ColumnTransformer`.
- `validation.pkl` no se lee ni se evalúa.

## Decisiones de consolidación

Pendiente de evaluar luego de la limpieza DAG. Por el momento no se modificó `decisions.md`.

## Riesgos residuales

- `01_Importacion_Datos.ipynb` confirma la lectura del CSV, pero no contiene el código de split; el notebook consolidado reproduce `train_test_split(test_size=0.30, random_state=42)` según DEC-004.
- La consolidación de categorías de `ult_actividad` se recalcula sobre el train, igual que el notebook de EDA. Al ejecutar, debe verificarse que las categorías resultantes sean compatibles con las categorías aprendidas por el preprocesador.
