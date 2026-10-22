# Registro de Decisiones Técnicas

Por qué se tomó cada decisión, el código ya explica qué se hizo.

**El razonamiento completo está en [`decisions_detalle.md`](decisions_detalle.md)** — mismos IDs y mismo orden.

---

## Índice

| ID | Área | Decisión |
|----|------|----------|
| DEC-001 | importacion | Integrar la única fuente sin merge ni concat |
| DEC-002 | calidad-datos | Preservar faltantes informativos e imputar sin borrar evidencia |
| DEC-003 | eda | Explorar por tipo sin eliminar variables automáticamente |
| DEC-004 | importacion | Dividir train/validación 70/30 reproduciblemente |
| DEC-005 | calidad-datos | Recortar extremos con umbrales explícitos aprobados |
| DEC-006 | feature-engineering | Congelar la estrategia de transformaciones para regresión logística |
| DEC-007 | seleccion-variables | Preseleccionar 40 variables con RFECV y correlación |
| DEC-008 | modelado | No aplicar balanceo de clases |
| DEC-009 | modelado | Congelar la configuración candidata de modelización |
| DEC-010 | despliegue | Consolidar preproducción con artefactos congelados |
| DEC-011 | despliegue | Fijar entorno y persistir reglas categóricas de inferencia |
| DEC-012 | despliegue | Reentrenar únicamente la familia logística disponible (reemplazada por DEC-016) |
| DEC-013 | despliegue | Exponer scoring mediante API REST con contrato explícito |
| DEC-014 | seleccion-variables | Mantener `ult_actividad` y `ocupacion` tras auditar posible leakage con el bivariante |
| DEC-015 | feature-engineering | Agrupar categorías raras de `ocupacion` y `ambito` (propuesta) |
| DEC-016 | despliegue | Alinear producción con el contrato de los notebooks (reemplaza DEC-012) |
| DEC-017 | despliegue | Explicar el score de forma exacta frente a un lead promedio (`POST /explain`) |
| DEC-018 | despliegue | Exponer el scoring a clientes de IA mediante un servidor MCP sin lógica de modelo |

---

## Pendientes reales

| Decisión | Área |
|---|---|
| Aplicar DEC-015 en `04_Transformacion` y repetir la cadena 04 → 05 → 07 → 08, luego `01_reentrenamiento.py`, `generar_referencia` y `03_evaluar_validacion.py` (regenera `preprocesador.joblib`, `01_reglas_categorias.json`, el artefacto y la API) | feature-engineering |
| Calibrar el corte `0,5` con costo y beneficio del contacto comercial | negocio |
| `POST /predict` con lista vacía lanza `KeyError` y acepta `visitas_total` negativo (defectos previos, no corregidos) | api |
| Migrar el servidor MCP a `mcp` 2.x (`FastMCP` pasó a `MCPServer`; hoy fijado en `mcp==1.30.0`) | mcp |

---

## Decisiones

**DEC-001 — Integración de fuentes.** Se mantuvo `Leads.csv` como única tabla y se asignó `df = leads.copy()`. **Por qué:** solo existía una fuente importable. **Regla:** analizar siempre grano y clave antes de integrar nuevas fuentes.

**DEC-002 — Política de faltantes y categorías.** Se preservaron scores faltantes, se imputaron faltantes categóricos/numéricos y se normalizó `google` a `Google`. **Por qué:** los faltantes de scores son estructurales y 63 de las 92 filas con faltantes de actividad tenían compra. **Regla:** preservar faltantes con significado e imputar con parámetros de train.

**DEC-003 — Criterios de tipeo y lectura exploratoria.** Se analizó el tablón por tipo y por lotes, agrupando las categorías minoritarias de `fuente` y las categorías de `ult_actividad` bajo 2% como `Otros`, sin tratar `id` como predictor. **Por qué:** esto mejora la lectura sin eliminar evidencia relevante y mantiene separada la exploración de la selección. **Regla:** explorar primero, agrupar categorías solo con un criterio explícito y seleccionar variables mediante una decisión posterior.

**DEC-004 — División entrenamiento-validación.** Se utilizó `train_test_split` 70/30 con `random_state=42`, sin IDs compartidos. **Por qué:** `id` era única y no había grupos repetidos. **Regla:** mantener una validación independiente y reproducible.

**DEC-005 — Recorte de extremos de comportamiento.** Se eliminaron 5 filas con `visitas_total > 30` o `paginas_vistas_visita > 20`. **Por qué:** eran valores extremadamente aislados según el análisis descendente. **Regla:** recortar solo con umbrales explícitos, documentados y aprobados.

**DEC-006 — Estrategia de feature engineering.** Se congeló la matriz: One-Hot con `drop="first"` para categóricas, exclusión de `id` y constantes, Yeo-Johnson más MinMaxScaler para comportamiento, e imputación mediana con un indicador estructural no redundante más MinMaxScaler para scores. **Por qué:** preservar interpretabilidad en regresión logística, llevar numéricas a 0–1 y evitar multicolinealidad perfecta. **Regla:** conservar solo versiones finales, no escalar dummies ni flags, eliminar indicadores duplicados y reutilizar el preprocesador ajustado sobre train.

**DEC-007 — Preselección supervisada de variables.** Se aplicó RFECV estándar con regresión logística L1 y se redujo de 52 a 43 variables; con umbral de correlación 0,70 se eliminaron `visitas_total_yj_mm`, `origen_Lead Add Form` y `ocupacion_Unemployed`, quedando 40 predictoras. **Por qué:** priorizar un conjunto más compacto para el modelo lineal sin eliminar grupos One-Hot completos ni variables por intuición. **Regla:** repetir RFECV y revisar correlaciones con validación cruzada antes de incorporar nuevos tablones.

---

**DEC-008 — No aplicar balanceo y fijar entrada de modelización.** Dado que `compra` presenta una proporción positiva aproximada del 37%, no se ejecutará la skill de balanceo de clases. El agente de modelización trabajará con `02_datos/03_Entrenamiento/05_train_tablon_preseleccion.pkl`, generado por la preselección supervisada.


**DEC-009 ? Configuración candidata de modelización.** Se congeló `LogisticRegression` con `C=14.528246637516036`, `penalty="l2"`, `solver="saga"` y `max_iter=5000`, seleccionada por ROC AUC medio 0,8919 con 5-fold StratifiedKFold sobre una muestra estratificada del 80%. Recall, precisión, F1 y accuracy quedan como métricas complementarias. La validación externa se realizará posteriormente sobre `02_datos/02_Validacion/validation.pkl`. **Regla:** usar la configuración persistida para el entrenamiento de producción y no usar la validación externa durante la selección.

**DEC-010 — Consolidación de preproducción.** Se integró el flujo en `08_Preproduccion.ipynb` usando el preprocesador ajustado, las 40 variables finalistas y la configuración logística congelada, sin reconstruir transformadores ni evaluar `validation.pkl`. **Por qué:** los artefactos ya codifican la transformación y el modelo aprobados; el notebook 01 solo confirma la lectura del CSV, mientras que el split 70/30 con `random_state=42` está documentado en DEC-004. **Regla:** en consolidaciones estáticas, reutilizar los contratos de artefactos y documentar cualquier paso cuya implementación fuente no esté disponible. **Aclarada por DEC-016:** ese contrato es el que ejecuta producción.


**DEC-011 — Reproducibilidad y reglas categóricas.** Se fijó el runtime en equirements.txt con scikit-learn==1.9.1 y dependencias asociadas, y se persistió 1_reglas_categorias.json con las categorías raras de ult_actividad y la consolidación de uente. **Por qué:** el preprocesador fue serializado con scikit-learn 1.9.1 y una regla calculada por frecuencia no puede recalcularse sobre cada lead nuevo. **Regla:** reentrenar las reglas solo sobre train, persistirlas junto al modelo y cargarlas sin recalcular en inferencia.

**DEC-012 — Búsqueda de reentrenamiento.** Se reentrenará con LogisticRegression y búsqueda aleatoria de C y penalización L1/L2. **Por qué:** anking_modelos.csv contiene solo configuraciones logísticas; no se inventan familias sin evidencia comparativa. **Regla:** incorporar nuevas familias únicamente después de evaluarlas y persistir su ranking.

**DEC-013 — API REST de scoring.** Se expone `POST /predict` en FastAPI con entrada en lista JSON y salida `id`, `score` y `prediccion`; no se incorpora segmentación HOT/WARM/COLD. **Por qué:** se prioriza un contrato simple, trazable y alineado con el motor productivo. **Regla:** rechazar con HTTP 422 los registros que superen los extremos aprobados, para evitar que una fila quede sin respuesta silenciosamente.

**DEC-014 — Lectura bivariante y auditoría de leakage.** Se incorporó al EDA el análisis bivariante contra `compra` y se auditaron `ult_actividad` (IV 0,78) y `ocupacion` (IV 0,94), que superan el IV de 0,5 usado como alerta de leakage. Quitar `ult_actividad` baja el ROC AUC de CV de 0,8947 a 0,8581, quitar `ocupacion` a 0,8799 y quitar ambas a 0,8376. Se mantienen ambas variables bajo el supuesto de scoring durante el seguimiento. **Por qué:** `ocupacion` y `SMS Sent` conservan su señal dentro de estratos de engagement y de origen, pero esos controles no distinguen señal legítima de fuga; sin fecha ni acceso a negocio el riesgo no puede descartarse. **Regla:** ante variables con IV o AUC extremo, medir la dependencia del modelo (ablación), documentar el supuesto de momento de scoring y reportar el AUC conservador junto al AUC base.

**DEC-015 — Categorías raras en ocupacion y ambito (propuesta).** Se propone agrupar bajo `Otros` las categorías con frecuencia menor al 1% en `ocupacion` y `ambito`. **Por qué:** `Housewife` (7 filas, 100% de compra) entra al modelo con un coeficiente inestable, y el criterio ya se aplicó a `fuente` y `ult_actividad` (DEC-003). **Regla:** aplicar el mismo umbral de frecuencia mínima a todas las nominales y persistirlo en `01_reglas_categorias.json`; ejecutar junto con la repetición de la cadena 04 → 05 → 07 → 08.

**DEC-016 — Producción alineada con los notebooks.** `07_despliegue/01_reentrenamiento.py` pasa a seguir el contrato de `00_manifiesto_preproduccion.json`: reglas de calidad y categorías, `preprocesador.joblib` congelado, las 40 variables de `Variables_preseleccionadas.txt` y `LogisticRegression` (C=14,5282, L2, saga) entrenada solo con el 70% (split `random_state=42`); no hay búsqueda de hiperparámetros. Reemplaza DEC-012. **Por qué:** el 18/09 el script de producción se apartó del contrato (12 datos y 59 columnas, L1 con C=1,35, entrenado con el 100% de los leads), de modo que README, DEC-007/009/010 y la auditoría de leakage describían un modelo que no estaba desplegado y no existía una validación externa limpia. **Resultado:** evaluación única sobre `validation.pkl` (2.722 leads): ROC AUC 0,887, precisión 0,776 y recall 0,714 con corte 0,5. **Supuestos:** faltantes en `origen`, `no_enviar_email` y `descarga_lm` se codifican como "Desconocido" (ceros, igual que la categoría de referencia); `tiempo_en_site_total` faltante usa la mediana de train; las columnas que la API no recibe (`no_llamar`, `conociste_*`) se completan con "No". **Regla:** un solo camino de producción; cambiar el modelo desplegado exige cambiar el contrato y reevaluar; evaluar en `validation.pkl` una sola vez y no ajustar después; regenerar `referencia_explicacion.json` tras cada reentrenamiento.

**DEC-017 — Explicabilidad exacta frente a un lead promedio.** Se agregó `POST /explain`, que descompone el logit de la regresión logística en el aporte de cada una de las 12 variables originales y lo mide **frente a un lead promedio**: logit = `logit_referencia` + suma de contribuciones, con error de punto flotante. La referencia (`07_despliegue/api/referencia_explicacion.json`) se calcula con los 6.360 leads de entrenamiento y guarda el hash del artefacto; si no coincide con el modelo, `/explain` falla con un mensaje que indica regenerarla. **Por qué:** los términos crudos del logit se miden contra un cero arbitrario (las variables están escaladas), de modo que el score_actividad de un lead típico aparecía como "×344 las chances" cuando la diferencia real contra el promedio es ×1,6; la versión sin centrar era engañosa. **Regla:** toda explicación se expresa frente al lead promedio; tras reentrenar hay que ejecutar `python -m api.generar_referencia`. El aporte es del modelo, no causal.

**DEC-018 — Servidor MCP sin lógica de modelo.** `07_despliegue/mcp_server/` expone `score_lead`, `score_leads`, `explain_score` y `check_api_health`, y los recursos `leadscoring://variables` y `leadscoring://ficha-modelo`. Es una capa fina que llama a la API (`SCORING_API_URL`); no calcula nada ni duplica reglas. **Por qué:** permitir que usuarios no técnicos consulten el modelo desde un cliente de IA sin tocar la API, manteniendo una sola fuente de verdad para los scores. **Regla:** la ficha del modelo (`ficha_modelo.md`) se actualiza a mano con `evaluacion_validacion.json` tras cada reentrenamiento (las cifras no se actualizan solas) y un test falla si sus parámetros, o su AUC, precisión y recall, dejan de coincidir con el modelo y con ese JSON; la versión de `mcp` queda fijada en 1.x porque 2.x renombró `FastMCP`.
