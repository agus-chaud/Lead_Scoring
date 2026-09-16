# Informe de modelización - Lead Scoring

## Objetivo y problema

El objetivo es priorizar leads con mayor probabilidad de `compra`, manteniendo interpretabilidad para el equipo comercial. El problema es de clasificación binaria.

## Datos y validación

- Dataset: `C:\Users\Dell\Agus\Master Agentic DS\Lead_Scoring\02_datos\03_Entrenamiento\05_train_tablon_preseleccion.pkl`
- Filas totales: 6360
- Muestra estratificada: 5088 filas
- Positivos (`compra=1`): 37.48%
- Búsqueda: 4070 filas
- Interpretabilidad: 1018 filas reservadas
- Validación externa reservada: `02_datos/02_Validacion/validation.pkl`

## Algoritmo y experimento

Se evaluó `LogisticRegression` con `RandomizedSearchCV`, 30 configuraciones, `StratifiedKFold` de 5 folds y `roc_auc` como métrica principal. Se buscaron `C` y penalizaciones L1/L2 con `solver="saga"`, sin ponderación de clases.

## Ranking (top 10)

```text
         algoritmo  rank_test_roc_auc  mean_test_roc_auc  std_test_roc_auc  mean_test_recall  mean_test_precision  mean_test_f1  mean_test_accuracy                                 parametros
LogisticRegression                  1           0.891904          0.013579          0.735082             0.780994      0.757063            0.823096 {"C": 14.528246637516036, "penalty": "l2"}
LogisticRegression                  2           0.891862          0.013450          0.734426             0.779686      0.756110            0.822359  {"C": 55.51721685244721, "penalty": "l2"}
LogisticRegression                  3           0.891853          0.013455          0.734426             0.779686      0.756110            0.822359  {"C": 73.92266140516048, "penalty": "l1"}
LogisticRegression                  4           0.891709          0.013888          0.731803             0.779564      0.754700            0.821622 {"C": 3.4702669886504163, "penalty": "l2"}
LogisticRegression                  5           0.891539          0.013635          0.729836             0.777437      0.752661            0.820147 {"C": 1.1435780278433403, "penalty": "l1"}
LogisticRegression                  6           0.891473          0.013586          0.729836             0.777408      0.752655            0.820147 {"C": 1.0907475835157696, "penalty": "l1"}
LogisticRegression                  7           0.891460          0.013525          0.731148             0.778299      0.753744            0.820885 {"C": 0.9846738873614566, "penalty": "l1"}
LogisticRegression                  8           0.890856          0.014190          0.725246             0.780046      0.751445            0.820147 {"C": 1.2357483710912178, "penalty": "l2"}
LogisticRegression                  9           0.890740          0.014283          0.724590             0.779267      0.750750            0.819656 {"C": 1.1219752813215704, "penalty": "l2"}
LogisticRegression                 10           0.889953          0.013360          0.716066             0.778723      0.745829            0.817199 {"C": 0.4206039057901998, "penalty": "l1"}
```

## Configuración ganadora

- Algoritmo: `LogisticRegression`
- Parámetros: `{"C": 14.528246637516036, "max_iter": 5000, "penalty": "l2", "random_state": 42, "solver": "saga"}`
- ROC AUC medio: 0.8919
- Desviación estándar ROC AUC: 0.0136
- Recall medio: 0.7351
- Precisión media: 0.7810
- F1 medio: 0.7571
- Accuracy media: 0.8231

## Interpretabilidad

Las variables con mayor valor absoluto de coeficiente fueron `score_actividad_mm`, `tiempo_en_site_total_yj_mm` y `ocupacion_Housewife`. Por permutation importance destacaron `ult_actividad_SMS Sent`, `tiempo_en_site_total_yj_mm` y `ult_actividad_Email Opened`. Un coeficiente positivo aumenta el log-odds estimado de compra; uno negativo lo reduce.

Gráficos: `06_resultados/Modelizacion/curvas_modelo.png`.

## Cierre

Las métricas son de validación cruzada sobre la muestra de entrenamiento. Un agente posterior entrenará el modelo de producción con esta configuración sobre los datos completos y evaluará sobre `validation.pkl`. La familia de árboles queda pendiente.
